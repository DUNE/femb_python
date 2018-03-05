/////////////////////////////////////////////////////////////////////
////                              
////  File: read_socket.dll            
////                                                                                                                                      
////  Author: Eric Raguzin			                  
////          eraguzin@bnl.gov	              
////  Created: 7/18/2017
////  Modified 7/18/2017
////  Description:  DLL for low level socket reads from the cold FPGA, specifically
////				for reading multiple sockets simulataneously. Meant to be called
////				through Python.
////					 		
////
/////////////////////////////////////////////////////////////////////
////
//// Copyright (C) 2017 Brookhaven National Laboratory
////
/////////////////////////////////////////////////////////////////////

#define MAX_NUM_THREADS 4
#define CHAR_BUFFER_LENGTH 100
#define FIFO_BUFFER_LENGTH 500
#define MAX_BYTES_PER_PACKET 9014

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h> 
#include <winsock2.h>
#include <Windows.h>
#include <stdint.h>
#include <strsafe.h>

#pragma comment(lib, "Ws2_32.lib")

///////////////////////////////////////////////////////
// GLOBAL VARIABLES
///////////////////////////////////////////////////////

/*
Arrays of the two indicators of the FIFO position.  Every new file's worth of packets will increment the read position by 1,
and every time the file is written to disk, the write position increments by one.  In this way, the read thread can keep reading
and whenever the write thread is not caught up, it'll be writing.  Rather than have these loop to 0 when the buffer does, it's useful
to have an absolute count of how many times you're read/written for debugging.  If we're getting packets at 1 kHz, they shouldn't 
overflow until it's been running for 50 days.
*/

uint32_t global_read_position[MAX_NUM_THREADS] = {0};
uint32_t global_write_position[MAX_NUM_THREADS] = {0};

// The actual char buffer that the data is stored in.  Buffer more positions for packets than needed, so it can be fine tuned through Python.
char* global_fifo_buffer[MAX_NUM_THREADS][FIFO_BUFFER_LENGTH];

uint16_t global_n[MAX_NUM_THREADS] = {0};

// Since there's no bools in C
uint8_t global_enable_write[MAX_NUM_THREADS] = {0};
uint8_t global_enable_reads = 1;

// Global variables meant to be set by Python
uint32_t global_packets_to_read;
uint8_t global_packets_per_file;
uint16_t global_buffer_size;
uint16_t global_udp_port;
char* global_directory;

///////////////////////////////////////////////////////
// CUSTOM STRUCTURES
///////////////////////////////////////////////////////

// Basically just giving every thread it's own designator for which chip it represents and which IP it's using

typedef struct MyData {
    int chip_identifier;
	char* IP;
} MYDATA, *PMYDATA;

///////////////////////////////////////////////////////
// FUNCTION DECLARATIONS
///////////////////////////////////////////////////////

__declspec(dllexport) int socket_read_main(uint32_t packets_to_read,
											uint8_t chips_to_use,
											uint8_t packets_each_file,
											uint16_t buffers,
											uint16_t udp_port,
											wchar_t *PC_IP1,
											wchar_t *PC_IP2,
											wchar_t *PC_IP3,
											wchar_t *PC_IP4,
											wchar_t *save_directory);
__declspec(dllexport) int end_data_collection();
DWORD WINAPI write_packet_thread( LPVOID lpParam );
DWORD WINAPI get_packet_thread( LPVOID lpParam );
void ErrorHandler(LPTSTR lpszFunction); 

///////////////////////////////////////////////////////
// MAIN FUNCTION
///////////////////////////////////////////////////////

// Python call must pass in:
// The amount of total packets to read (0 means go until Python externally tells it to stop)
// The amount of chips to use (in case certain chips or ethernet connections are down)
// Packets to concatenate per file.  Should be at least two, or else the PC can't write 1000 3kB files per second.  Even 500 6 kB files is doable
// Buffer size of the FIFO.  Should be 50 at the most.  If it ever increases significantly, something is wrong anyway
// The port that the FPGA will be writing to
// All 4 FPGA IP addresses that will be read
// Directory to save the data/debug files to

int socket_read_main(uint32_t packets_to_read,
						uint8_t chips_to_use,
						uint8_t packets_each_file,
						uint16_t buffers,
						uint16_t udp_port,
						wchar_t *PC_IP1,
						wchar_t *PC_IP2,
						wchar_t *PC_IP3,
						wchar_t *PC_IP4,
						wchar_t *save_directory)
{  
	// A pointer to the WSADATA data structure that is to receive details of the Windows Sockets implementation.
	WSADATA wsaData;

	typedef unsigned long DWORD;

	// Argument, return value and handle arrays for threading
	PMYDATA pDataArray_read_thread[MAX_NUM_THREADS];
    DWORD   dwThreadIdArray_read_thread[MAX_NUM_THREADS];
    HANDLE  hThreadArray_read_thread[MAX_NUM_THREADS]; 

    int err, i, j, resp, num_of_chars;
	char directory[CHAR_BUFFER_LENGTH];
	char debug_filename[CHAR_BUFFER_LENGTH];
	char debug_text[CHAR_BUFFER_LENGTH * 10];
	char* PC_IP_Address[4];

	FILE* argument_file;

	// Sets necessary global variables that will be used by all threads
	global_packets_to_read = packets_to_read;
	global_packets_per_file = packets_each_file;
	global_buffer_size = buffers;
	global_udp_port = udp_port;
	global_directory = directory;

	// Allocates some memory to turn the PC IP addresses from a wchar to a string
	for (i=0; i<4; i++)
	{
		PC_IP_Address[i] = (char*)malloc(sizeof(char) * CHAR_BUFFER_LENGTH);
	}

	sprintf_s(PC_IP_Address[0], CHAR_BUFFER_LENGTH, "%s", PC_IP1);
	sprintf_s(PC_IP_Address[1], CHAR_BUFFER_LENGTH, "%s", PC_IP2);
	sprintf_s(PC_IP_Address[2], CHAR_BUFFER_LENGTH, "%s", PC_IP3);
	sprintf_s(PC_IP_Address[3], CHAR_BUFFER_LENGTH, "%s", PC_IP4);
	sprintf_s(directory, sizeof(directory),"%s", save_directory);


	// Print some initial info about what was passed into here for later reference
	sprintf_s(debug_filename,sizeof(debug_filename), "%sC Argument Info.txt", directory);
	resp = fopen_s(&argument_file,debug_filename, "w");

	if ((!argument_file) ^ (resp != 0))
	{
		printf("Unable to open file!");
		return 1;
	}

	num_of_chars = sprintf_s(debug_text, sizeof(debug_text), 
		"Total Packets: %d\nNumber of Chips: %d\nPackets per File: %d\nBuffer Size: %d\nPort: %d\nIP1: %s\nIP2: %s\nIP3: %s\nIP4: %s\nDirectory: %s", 
		global_packets_to_read, chips_to_use, global_packets_per_file, global_buffer_size, global_udp_port, 
		PC_IP_Address[0], PC_IP_Address[1], PC_IP_Address[2], PC_IP_Address[3], directory);
	fwrite(debug_text, 1, num_of_chars, argument_file);
	fclose(argument_file);

	
	// Starts version 2.2 of Windows Socket DLL
	err = WSAStartup(MAKEWORD(2,2), &wsaData);

    if (err != 0) {
        printf("WSAStartup failed with error: %d\n", err);
        return -1;
    }

	/////////////////////////////////////////////
	//Create Socket Read Threads
	/////////////////////////////////////////////

	for( i=0; i<chips_to_use; i++ )
    {
        // Allocate memory for input data that will be passed in to each thread

        pDataArray_read_thread[i] = (PMYDATA) HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY,
                sizeof(MYDATA));

        if( pDataArray_read_thread[i] == NULL )
        {
           // If the array allocation fails, the system is out of memory
           // so there is no point in trying to print an error message.
           // Just terminate execution.
            ExitProcess(2);
        }

        // Each thread needs to know which chip it represents (so it knows which arrays to access) and which IP address it'll read from

        pDataArray_read_thread[i]->chip_identifier = i;
		pDataArray_read_thread[i]->IP			   = PC_IP_Address[i];

		// Allocate memory for each chip's buffer position for the worst case scenario - the maximum size jumbo UDP packet coming in
		// calloc actually sets every position to 0, so it takes a bit longer than malloc, but the position is ready to be written to immediately
		for (j=0;j<global_buffer_size;j++)
			{
				global_fifo_buffer[i][j] = (char *) calloc (1, MAX_BYTES_PER_PACKET * global_packets_per_file);

			}

        // Create the socket read thread to begin execution on its own.
        hThreadArray_read_thread[i] = CreateThread( 
            NULL,                   // default security attributes
            0,                      // use default stack size  
            get_packet_thread,		// thread function name
            pDataArray_read_thread[i],          // argument to thread function 
            0,                      // use default creation flags 
            &dwThreadIdArray_read_thread[i]);   // returns the thread identifier 

		// So far, setting it to maximum priority has worked.  If the computer is better, maybe we can try lowering the thread priority
		SetThreadPriority(
		  hThreadArray_read_thread[i],
		  THREAD_PRIORITY_TIME_CRITICAL
		);

        // Check the return value for success.
        // If CreateThread fails, terminate execution. 
        // This will automatically clean up threads and memory. 
        if (hThreadArray_read_thread[i] == NULL) 
        {
           ErrorHandler(TEXT("CreateThread"));
           ExitProcess(3);
        }
    }

	////////////////////////////////////////
	//Wait and clean up
	////////////////////////////////////////

	// Once all the read threads have been created, the main thread will block until all read threads have completed
	WaitForMultipleObjects(chips_to_use, hThreadArray_read_thread, TRUE, INFINITE);

    // Close all thread handles and free memory allocations.
    for(i=0; i<chips_to_use; i++)
    {
        CloseHandle(hThreadArray_read_thread[i]);
        if(pDataArray_read_thread[i] != NULL)
        {
            HeapFree(GetProcessHeap(), 0, pDataArray_read_thread[i]);
            pDataArray_read_thread[i] = NULL;    // Ensure address is not reused.
        }
    }

    // Clean up and exit.
    WSACleanup();
    return 0;

	
	
}   

//////////////////////////////////////////
// Read Thread
//////////////////////////////////////////

DWORD WINAPI get_packet_thread( LPVOID lpParam ){

	PMYDATA pDataArray_internal;
	SOCKET PC_socket;
	int resp, chip, num_of_chars, times_through;
	struct sockaddr_in serv_addr;
	char buffer[MAX_BYTES_PER_PACKET];
	char* PC_IP_Address;
	char debug_filename[CHAR_BUFFER_LENGTH];
	char debug_text[CHAR_BUFFER_LENGTH];

	//Since this thread needs to start it's own unique write thread
	PMYDATA pDataArray_write_thread;
    DWORD   dwThreadIdArray_write_thread;
    HANDLE  hThreadArray_write_thread; 

	FILE* read_thread_file;

	struct sockaddr_in SenderAddr;
    int SenderAddrSize = sizeof (SenderAddr);

	// Receives thread specific data that was passed in
	pDataArray_internal = (PMYDATA)lpParam;
	PC_IP_Address = pDataArray_internal->IP;
	chip		  =	pDataArray_internal->chip_identifier;

	////////////////////////////////////////
	// Print out some debug info 
	////////////////////////////////////////

	sprintf_s(debug_filename,sizeof(debug_filename), "%sRead_Thread_Chip%d.txt", global_directory, chip);
	resp = fopen_s(&read_thread_file,debug_filename, "w");

	if (!read_thread_file ^ (resp != 0))
		{
			printf("Unable to open file!");
			return 1;
		}

	num_of_chars = sprintf_s(debug_text, sizeof(debug_text), "This is chip %d\n", chip);
	fwrite(debug_text, 1, num_of_chars, read_thread_file);

	num_of_chars = sprintf_s(debug_text, sizeof(debug_text), "And it's using an IP of %s\n", PC_IP_Address);
	fwrite(debug_text, 1, num_of_chars, read_thread_file);

	fclose(read_thread_file);

	////////////////////////////////////////
	// Prepare Socket
	////////////////////////////////////////

	//Start a socket for IPv4, Datagrams, and specifically UDP
    PC_socket = socket (AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (PC_socket == INVALID_SOCKET) {
        printf ("Error %d opening socket.\n", errno);
        return -1;
    }

	serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(global_udp_port);
	serv_addr.sin_addr.s_addr = inet_addr(PC_IP_Address);

	// Set all bits of the padding field to 0
	memset(serv_addr.sin_zero, '\0', sizeof serv_addr.sin_zero);

	//Bind the socket to the IP Address and incoming port specified
	resp = bind(PC_socket, (struct sockaddr *) &serv_addr, sizeof(serv_addr));
	if (resp != 0) {
        printf ("Error %d binding socket.\n", errno);
        return -1;
    }

	//Played around with the idea of adding a timeout, but maybe it's better not to as of now
	//if(setsockopt(PC_socket, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)))

	////////////////////////////////////////
	//Start Write Thread
	////////////////////////////////////////

	// Allocate memory for write thread data.
    pDataArray_write_thread = (PMYDATA) HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY,
            sizeof(MYDATA));

    if( pDataArray_write_thread == NULL )
    {
        ExitProcess(2);
    }

    // The write thread really only needs to know the chip number, but I'll complete the struct anyway
    pDataArray_write_thread->chip_identifier = chip;
	pDataArray_write_thread->IP				 = PC_IP_Address;

    // Create the write thread to begin execution on its own.
    hThreadArray_write_thread = CreateThread( 
    NULL,								// default security attributes
    0,									// use default stack size  
    write_packet_thread,				// thread function name
    pDataArray_write_thread,			// argument to thread function 
    0,									// use default creation flags 
    &dwThreadIdArray_write_thread);     // returns the thread identifier 

    if (hThreadArray_write_thread == NULL) 
    {
        ErrorHandler(TEXT("CreateThread"));
        ExitProcess(3);
    }

	// Setting the priority doesn't really help to solve the problem of bottlenecking at the write to hard disk
	//SetThreadPriority(
	//	hThreadArray_write_thread,
	//	THREAD_PRIORITY_TIME_CRITICAL
	//);

	// The idea was to be able to control when the write thread is allowed to write or not.  In practice it should always be on, because decides to write based on buffer position
	global_enable_write[chip] = 1;

	////////////////////////////////////////
	// Read incoming packets
	////////////////////////////////////////

	// If the user put "0" packets to read, that means they want to run it until Python tells the DLL to stop, so this will run infinitely in a while loop until it's told not to
	if (global_packets_to_read == 0)
	{
		while (global_enable_reads == 1)
		{
			// This will read in a loop to concatenate files into a single buffer that will get written to file.  Increasing the FIFO position (global_read_position) by 1
			// means that an entire file is ready to be written.  So every FIFO position is actually representative of a single file of multiple packets

			// The actual recvfrom statement is a little complicated, it's a triple char array.  The first dimension is the chip used.  The next dimension is the buffer position.
			// Once it loops through the buffer size (say 50), the modulus operator means it will go back to the original position.  The last dimension is written so that when
			// concatenating packets, the next packet will start at an offset of the length of the previous write, at the byte after the last one was written, but still
			// in the same continuous buffer so it can all be written to file at once.  The & is there because the recvfrom function wants a pointer to all of that.
			for (times_through = 0; times_through < global_packets_per_file; times_through++)
			{
				global_n[chip] = recvfrom(PC_socket,&global_fifo_buffer[chip][(global_read_position[chip]) % global_buffer_size][global_n[chip] * times_through],
									sizeof(buffer),
									0,
									(SOCKADDR *) & SenderAddr,
									&SenderAddrSize);

				if (global_n[chip] == SOCKET_ERROR) 
				{
					wprintf(L"recvfrom failed with error %d\n", WSAGetLastError());
				}
			}

			global_read_position[chip]++;
		}
	}

	// If an actual number was given for maximum packets, it'll be a for loop that runs for that amount of packets
	else
	{
		// Again, each global_read_position is indicative of multiple packets in a single file, so everything needs to be adjusted to that
		for (global_read_position[chip]; global_read_position[chip] < (global_packets_to_read/global_packets_per_file); global_read_position[chip]++)
		{
			for (times_through = 0;times_through<global_packets_per_file;times_through++)
			{
				global_n[chip] = recvfrom(PC_socket,&global_fifo_buffer[chip][(global_read_position[chip]) % global_buffer_size][global_n[chip] * times_through],
									sizeof(buffer),
									0,
									(SOCKADDR *) & SenderAddr,
									&SenderAddrSize);

				if (global_n[chip] == SOCKET_ERROR) 
				{
					wprintf(L"recvfrom failed with error %d\n", WSAGetLastError());
				}
			}

			//Even if it's going for a set amount of packets, if Python tells it to stop, it'll stop
			if (global_enable_reads == 0)
			{
				break;
			}
		}
	}

	////////////////////////////////////////
	// Clean up read thread
	////////////////////////////////////////

	// This is after the actual socket reading has finished.  If the write part of the FIFO hasn't caught up yet, it'll wait for everything to be written to disk
	// While giving status updates every half second for debugging
	while (global_write_position[chip] != global_read_position[chip])
	{
	Sleep(500);
	resp=fopen_s(&read_thread_file,debug_filename,"a");
	num_of_chars = sprintf_s(debug_text, sizeof(debug_text), "Waiting to close out because read is %d and write is %d\n", global_read_position[chip], global_write_position[chip]);
	fwrite(debug_text, 1, num_of_chars, read_thread_file);
	fclose(read_thread_file);
	}

	// Just a final printout check to make sure everything worked the way it should
	resp=fopen_s(&read_thread_file,debug_filename,"a");
	num_of_chars = sprintf_s(debug_text, sizeof(debug_text), "In the end, read is %d and write is %d\n", global_read_position[chip], global_write_position[chip]);
	fwrite(debug_text, 1, num_of_chars, read_thread_file);
	fclose(read_thread_file);

	// Stop the write thread from waiting for the FIFO to increment anymore.  Then when it closes, free memory allocation
	global_enable_write[chip] = 0;
	WaitForSingleObject(hThreadArray_write_thread, INFINITE);
    CloseHandle(hThreadArray_write_thread);
    if(pDataArray_write_thread != NULL)
    {
        HeapFree(GetProcessHeap(), 0, pDataArray_write_thread);
        pDataArray_write_thread = NULL;    // Ensure address is not reused.
    }

    // Close the socket when finished
    wprintf(L"Finished receiving. Closing socket.\n");
    resp = closesocket(PC_socket);
    if (resp == SOCKET_ERROR) {
        wprintf(L"closesocket failed with error %d\n", WSAGetLastError());
        return 1;
    }
	
	return 0;
}

////////////////////////////////////////
// Write Thread
////////////////////////////////////////

DWORD WINAPI write_packet_thread( LPVOID lpParam ){
	FILE *write_thread_debug_file;
	FILE *write_thread_write_file;
	PMYDATA pDataArray_internal;
	int num_of_chars, resp, chip;
	char filename[CHAR_BUFFER_LENGTH];
	char debug_filename[CHAR_BUFFER_LENGTH];
	char debug_text[CHAR_BUFFER_LENGTH];

	// Receives thread specific data that was passed in
	pDataArray_internal = (PMYDATA)lpParam;
	chip = pDataArray_internal->chip_identifier;


	sprintf_s(debug_filename,sizeof(debug_filename), "%sWrite_Thread_Chip%d.txt", global_directory, chip);

	while(global_enable_write[chip])
	{
		// Continually waits for a full file of multiple packets that it hasn't already written
		if (global_write_position[chip] < global_read_position[chip])
		{
			// First 4 bytes of an FPGA packet are the packet number.  This is the quickest way I was able to convert that into a decimal packet number
			uint8_t packet_number0 = (global_fifo_buffer[chip][global_write_position[chip] % global_buffer_size][8]);
			uint8_t packet_number1 = (global_fifo_buffer[chip][global_write_position[chip] % global_buffer_size][9]);
			uint8_t packet_number2 = (global_fifo_buffer[chip][global_write_position[chip] % global_buffer_size][10]);
			uint8_t packet_number3 = (global_fifo_buffer[chip][global_write_position[chip] % global_buffer_size][11]);

			uint32_t packet_number = packet_number3 + (packet_number2 * 256) + (packet_number1 * 65536) + (packet_number0 * 16777216);

			/* Debugging
			if (global_write_position[chip] % 100 == 0)
			{
				resp=fopen_s(&write_thread_debug_file,debug_filename,"a");
				num_of_chars = sprintf_s(debug_text, sizeof(debug_text), "This was done because read is %d and write is %d\n", global_read_position[chip], global_write_position[chip]);
				fwrite(debug_text, 1, num_of_chars, write_thread_debug_file);
				num_of_chars = sprintf_s(debug_text, sizeof(debug_text), "And packet num is %d and position in fifo is %d\n", packet_number, global_write_position[chip] % global_buffer_size);
				fwrite(debug_text, 1, num_of_chars, write_thread_debug_file);
				fclose(write_thread_debug_file);
				
			}
			*/

			// Create the file name based on that packet number and the chip
			sprintf_s(filename, sizeof(filename), "%sChip%d_Packet%d.dat", global_directory, chip, packet_number);

			resp=fopen_s(&write_thread_write_file,filename,"wb");
			if (!write_thread_write_file)
				{
					printf("Unable to open file!");
					return 1;
				}

			// Since we know the position of the buffer we want to write, we write the size of a single packet (global_n, the return value from the recvfrom function
			// which SHOULD always be the same) the amount of times that we've concatenated a packet in the buffer
			fwrite(global_fifo_buffer[chip][global_write_position[chip] % global_buffer_size], global_n[chip], global_packets_per_file, write_thread_write_file);
			fclose(write_thread_write_file);
			

			global_write_position[chip]=global_write_position[chip] + 1;
		}
	}

	return 0;
}

////////////////////////////////////////
// End data collection/Stop DLL externally
////////////////////////////////////////

int end_data_collection()
{
	global_enable_reads = 0;
	return 0;
}

////////////////////////////////////////
// Error handler
////////////////////////////////////////

//Honestly, this is just an error handling function that was recommended on the Windows documentation about threads, I don't know too much about it

void ErrorHandler(LPTSTR lpszFunction) 
{ 
    // Retrieve the system error message for the last-error code.

    LPVOID lpMsgBuf;
    LPVOID lpDisplayBuf;
    DWORD dw = GetLastError(); 

    FormatMessage(
        FORMAT_MESSAGE_ALLOCATE_BUFFER | 
        FORMAT_MESSAGE_FROM_SYSTEM |
        FORMAT_MESSAGE_IGNORE_INSERTS,
        NULL,
        dw,
        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (LPTSTR) &lpMsgBuf,
        0, NULL );

    // Display the error message.

    lpDisplayBuf = (LPVOID)LocalAlloc(LMEM_ZEROINIT, 
        (lstrlen((LPCTSTR) lpMsgBuf) + lstrlen((LPCTSTR) lpszFunction) + 40) * sizeof(TCHAR)); 
    StringCchPrintf((LPTSTR)lpDisplayBuf, 
        LocalSize(lpDisplayBuf) / sizeof(TCHAR),
        TEXT("%s failed with error %d: %s"), 
        lpszFunction, dw, lpMsgBuf); 
    MessageBox(NULL, (LPCTSTR) lpDisplayBuf, TEXT("Error"), MB_OK); 

    // Free error-handling buffer allocations.

    LocalFree(lpMsgBuf);
    LocalFree(lpDisplayBuf);
}