//compile independently with: g++ -std=c++11 -o parseBinaryFile parseBinaryFile.cxx `root-config --cflags --glibs`
#include <iostream>
#include <fstream>
#include <sstream>
#include <cstdlib>
#include <arpa/inet.h>
using namespace std;

#include "TROOT.h"
#include "TMath.h"
#include "TApplication.h"
#include "TFile.h"
#include "TH1.h"
#include "TH2.h"
#include "TString.h"
#include "TCanvas.h"
#include "TSystem.h"
#include "TGraph.h"
#include "TProfile2D.h"
#include "TTree.h"

using namespace std;

//global TApplication object declared here for simplicity
TApplication *theApp;

class Analyze {
	public:
	Analyze(std::string inputFileName);
        int processFileName(std::string inputFileName, std::string &baseFileName);
	void doAnalysis();
	void parseFile();
	void parseRawData();
	void parseAsicRawData(unsigned int subrun, unsigned int asic);
	void drawWf(unsigned int subrun, unsigned int chan);

	//Files
	ifstream infile;
	TFile *gOut;

	//Constants
        const unsigned int maxNumAsic = 8;// 35t
	const unsigned int maxNumChan = 128;// 35t
        const unsigned int maxNumSubrun = 1024; //want to get rid of this

	//variables
	unsigned int maxSubrunParsed = 0;

	//data objects
	TCanvas* c0;
	TGraph *gCh;
	std::vector<unsigned short> asicPackets[1024][8]; //subrun, asics
	std::vector<unsigned short> wfIn[1024][128]; //subrun, ch

	//histograms

	//output tree and variable
	unsigned short fSubrun, fChan;
	std::vector<unsigned short> fWf;
	TTree *tTree;
};

Analyze::Analyze(std::string inputFileName){

	//get input file
	if( inputFileName.empty() ){
		std::cout << "Error invalid file name" << std::endl;
		gSystem->Exit(0);
	}

	infile.open(inputFileName, std::ifstream::in | std::ifstream::binary);  
        if (infile.fail()) {
		std::cout << "Error opening input file, exiting" << std::endl;
		gSystem->Exit(0);
	}

	//make output file
  	std::string outputFileName = "output_parseBinaryFile.root";
	//if( processFileName( inputFileName, outputFileName ) )
	//	outputFileName = "output_parseBinaryFile_" + outputFileName + ".root";

  	gOut = new TFile(outputFileName.c_str() , "RECREATE");

  	//initialize canvas
  	c0 = new TCanvas("c0", "c0",1400,800);

	//initialize graphs
	gCh = new TGraph();

	//output tree
	tTree = new TTree("femb_wfdata","femb_wfdata");
	tTree->Branch("subrun", &fSubrun, "subrun/s");
  	tTree->Branch("chan", &fChan, "chan/s");
	tTree->Branch("wf", "vector<unsigned short>", &fWf);
}

int Analyze::processFileName(std::string inputFileName, std::string &baseFileName){
        //check if filename is empty
        if( inputFileName.size() == 0 ){
                std::cout << "processFileName : Invalid filename " << std::endl;
                return 0;
        }

        //remove path from name
        size_t pos = 0;
        std::string delimiter = "/";
        while ((pos = inputFileName.find(delimiter)) != std::string::npos)
                inputFileName.erase(0, pos + delimiter.length());

	if( inputFileName.size() == 0 ){
                std::cout << "processFileName : Invalid filename " << std::endl;
                return 0;
        }

        //replace / with _
        std::replace( inputFileName.begin(), inputFileName.end(), '/', '_'); // replace all 'x' to 'y'
        std::replace( inputFileName.begin(), inputFileName.end(), '-', '_'); // replace all 'x' to 'y'

	baseFileName = inputFileName;
	
	return 1;
}

void Analyze::doAnalysis(){

        //parse the input file
    	parseFile();
	parseRawData();

	//save waveforms in output tree
	//for(int subrun = 0 ; subrun < maxNumSubrun ; subrun++ ){
	for(unsigned int subrun = 0 ; subrun <= maxSubrunParsed ; subrun++ ){
		std::cout << "Analsyzing data from subrun " << subrun << std::endl;
		for( unsigned int ch = 0 ; ch <maxNumChan ; ch++ ){
			//drawWf(subrun,ch);
			//fill tree
			fSubrun = subrun;
			fChan = ch;
			fWf = wfIn[subrun][ch];
			tTree->Fill();
		}
	}

    	gOut->Cd("");
	tTree->Write();
  	gOut->Close();
}

void Analyze::parseFile(){
    	// get length of file:
    	infile.seekg (0, infile.end);
    	unsigned int size_in_bytes = infile.tellg();
    	infile.seekg (0, infile.beg);

	//detect empty file
	if( size_in_bytes <= 10 ){
		std::cout << "Empty input file detected, exiting" << std::endl;
		return;
	}
    	std::cout << "Reading " << size_in_bytes << " bytes from file " << std::endl;

	//define buffer
    	char * buffer = new char [size_in_bytes];
	unsigned short *buffer_ushort = (unsigned short *) buffer;

    	// read data as a block:
    	infile.read (buffer,size_in_bytes);
    	if (infile) {
      		std::cout << "all characters read successfully." << std::endl;
    	} else {
      		std::cout << "error: only " << infile.gcount() << " could be read" << std::endl;
	}
    	infile.close();

	unsigned int sizeInUint32 = size_in_bytes/4;
	unsigned int sizeInUshort = size_in_bytes/2;

        //ASIC packet header
	unsigned short packetHeader[5];
        packetHeader[0] = 0x0;
        packetHeader[1] = 0xdead;
        packetHeader[2] = 0xbeef;
        packetHeader[3] = 0x0;
        packetHeader[4] = 0xba5e;

	//loop throiugh buffer, scan for packet headers
	unsigned int pos = 0;
	int asicNum = -1;
	int prevAsicNum = -1;
	std::vector<unsigned int> headerPos;
	for(unsigned int pos = 5 ; pos < sizeInUshort ; pos++ ){
		unsigned short dataWord = ntohs(buffer_ushort[pos]);
		//check for new header
		bool foundHeader = 0;
		if( ntohs(buffer_ushort[pos-5]) ==  packetHeader[0] &&
		    ntohs(buffer_ushort[pos-4]) ==  packetHeader[1] &&
		    ntohs(buffer_ushort[pos-3]) ==  packetHeader[2] &&
		    ntohs(buffer_ushort[pos-2]) ==  packetHeader[3] &&
		    ntohs(buffer_ushort[pos-1]) ==  packetHeader[4] ){
			headerPos.push_back(pos-5);
		}
	}

	if( headerPos.size() == 0 ){
		std::cout << "No packet headers detected, returning" << std::endl;
		return;
	}
        std::cout << "Number of packets " << headerPos.size() << std::endl;

	//loop through each packet, collect ASIC packets
	unsigned int prevSubrun = 0;
	for(unsigned int headNum = 0 ; headNum < headerPos.size() ; headNum++){
		//std::cout << "NEW HEADER " << headNum << "\t" << headerPos.at(headNum) << std::endl;
	
		unsigned int basePos = headerPos.at(headNum);
		if( basePos >= sizeInUshort )
			continue;

		unsigned int endPos = sizeInUshort-1;
		if( headNum < headerPos.size() - 1 )
			endPos = headerPos.at(headNum+1) - 1;

		if( endPos >= sizeInUshort )
			continue;

		unsigned int packetSize = endPos - basePos + 1;
		if( packetSize <= 9  )
			continue;

		//get subrun number
		unsigned short subrunNum = (unsigned short ) ntohs(buffer_ushort[basePos + 5]);
		//std::cout << "SUBRUN NUMBER " << subrunNum << std::endl;
		if( subrunNum >= maxNumSubrun ){
			std::cout << "Subrun # exceeded maximimum of " << maxNumSubrun << ", exiting. File parser should be written better." << std::endl;
			continue;
		}
		if( subrunNum != prevSubrun ){
			std::cout << "Collecting packets from subrun " << subrunNum << std::endl;
			prevSubrun = subrunNum;
		}
		if( subrunNum > maxSubrunParsed )
			maxSubrunParsed = subrunNum;

		//get ASIC number
		unsigned short asicNum = (unsigned short ) ntohs(buffer_ushort[basePos + 6]);
		//std::cout << "ASIC NUMBER " << asicNum << std::endl;
		if(  asicNum > maxNumAsic )
			continue;

		//get channel number
		unsigned short chanNum = (unsigned short ) ntohs(buffer_ushort[basePos + 7]);
		//std::cout << "CHANNEL NUMBER " << chanNum << std::endl;
		if(  chanNum > maxNumChan )
			continue;

		//get UDP packet number
		unsigned short packetNum = (unsigned short) ntohs(buffer_ushort[basePos + 9]);
		//std::cout << "PACKET NUMBER " << packetNum << std::endl;

		//store actual data in vector
		for( unsigned int line = basePos + 16 ; line <= endPos ;line++){
			unsigned short dataWord = (unsigned short) ntohs(buffer_ushort[line]);
			asicPackets[subrunNum][asicNum].push_back(dataWord);
			//if( line < basePos + 40 )
			//	std::cout << std::dec << line << "\t" << basePos << "\t" << endPos << "\t" << std::hex << dataWord << std::endl;
		}
		//char ct;
		//std::cin >> ct;
	}//end loop over headers
		
    	delete[] buffer_ushort;
}

void Analyze::parseRawData(){
	//loop over subruns
	//for(int subrun = 0 ; subrun < maxNumSubrun ; subrun++ ){
	for(int subrun = 0 ; subrun <= maxSubrunParsed ; subrun++ ){
		std::cout << "Parsing data from subrun " << subrun << std::endl;
		//loop over ASIC data packets
		for(int asic = 0 ; asic < maxNumAsic ; asic++ )
			parseAsicRawData(subrun,asic);
	}

	return;
}

void Analyze::parseAsicRawData(unsigned int subrun, unsigned int asic){
	if( subrun > maxNumSubrun || asic > maxNumAsic )
		return;
	if( asicPackets[subrun][asic].size() == 0 )
		return;

	//find 0xface words
	std::vector<unsigned int> facePos;
	for( unsigned int line = 0 ; line < asicPackets[subrun][asic].size() ; line++){
		//std::cout << asicPackets[subrun][asic].at(line) << std::endl;
		if( asicPackets[subrun][asic].at(line) == 0xface )
			facePos.push_back(line);
	}

	//require some minimum number of ASIC packets
	if( facePos.size() < 3  )
		return;

	//double check correct packet spacing
	if( facePos.at(1) - facePos.at(0) != 13 || facePos.at(2) - facePos.at(1) != 13 )
		return;
	unsigned int basePos = facePos.at(0);

	//loop through ASIC packets, ignore clipped packets
	unsigned int line = basePos;
	while(line < asicPackets[subrun][asic].size() ){

		//don't use clipped packets
		if( line + 13 >= asicPackets[subrun][asic].size() )
			break;

		unsigned short dataWord = asicPackets[subrun][asic].at(line);
		//std::cout << std::hex << dataWord << std::endl;
		if( dataWord != 0xface ){
			//std::cout << "Invalid ASIC packet header, breaking" << std::endl;
			break; //should always find ASIC packet headers
		}
		//get data words in ASIC packets
		//std::cout << "ASIC PACKET " << std::endl;
		short wordArray[12];
		for(int wordNum = 0 ; wordNum < 12 ; wordNum++){
			unsigned int lineNum = line+1+wordNum;
			if( lineNum >= asicPackets[subrun][asic].size() ) continue;
			wordArray[wordNum] = asicPackets[subrun][asic].at(lineNum);
			//std::cout << "\t" << std::dec << wordNum << "\t" << std::hex << wordArray[wordNum] << std::endl;
		}

		//update buffer position
		line = line + 13;

		//attempt to decode ASIC packet
		short chSamp[16] = {0};
		chSamp[0] = ((wordArray[5] & 0xFFF0 ) >> 4);
		chSamp[1] = ((wordArray[4] & 0xFF00 ) >> 8) | ((wordArray[5] & 0x000F ) << 8);
		chSamp[2] = ((wordArray[4] & 0x00FF ) << 4) | ((wordArray[3] & 0xF000 ) >> 12);
		chSamp[3] = ((wordArray[3] & 0x0FFF ) >> 0);
		chSamp[4] = ((wordArray[2] & 0xFFF0 ) >> 4);
		chSamp[5] = ((wordArray[2] & 0x000F ) << 8) | ((wordArray[1] & 0xFF00 ) >> 8);
		chSamp[6] = ((wordArray[1] & 0x00FF ) << 4) | ((wordArray[0] & 0xF000 ) >> 12);
		chSamp[7] = ((wordArray[0] & 0x0FFF ) >> 0);						
		chSamp[8] = ((wordArray[11] & 0xFFF0 ) >> 4) ;
		chSamp[9] = ((wordArray[11] & 0x000F ) << 8) | ((wordArray[10] & 0xFF00 ) >> 8) ;
		chSamp[10] = ((wordArray[10] & 0x00FF ) << 4) | ((wordArray[9] & 0xF000 ) >> 12) ;
		chSamp[11] = ((wordArray[9] & 0x0FFF ));
		chSamp[12] = ((wordArray[8] & 0xFFF0 ) >> 4);
		chSamp[13] = ((wordArray[8] & 0x000F ) << 8) | ((wordArray[7] & 0xFF00 ) >> 8) ;
		chSamp[14] = ((wordArray[7] & 0x00FF ) << 4) | ((wordArray[6] & 0xF000 ) >> 12) ;
		chSamp[15] = ((wordArray[6] & 0x0FFF ) );

		//std::cout << "PARSED SAMPLES " << std::endl;
		for(int ch = 0 ; ch < 16 ; ch++){
			//std::cout << asic << "\t" << ch << "\t" << std::hex << chSamp[ch] << "\t" << std::dec << chSamp[ch] << std::endl;
			int chNum = 16*asic + ch;
			if( chNum < 0 || chNum > 127 )
				continue;
			wfIn[subrun][chNum].push_back(chSamp[ch]);
		}
		//char ct;
		//std::cin >> ct;
	}//end loop over asic packets

	return;
}

void Analyze::drawWf(unsigned int subrun, unsigned int chan){
	gCh->Set(0);
	for( int s = 0 ; s < wfIn[subrun][chan].size() ; s++ )
		gCh->SetPoint(gCh->GetN() , s , wfIn[subrun][chan].at(s) );
	c0->Clear();
	gCh->Draw("ALP");
	c0->Update();
	usleep(100000);
	//char ct;
	//std::cin >> ct;

	return;
}

void parseBinaryFile(std::string inputFileName) {

  Analyze ana(inputFileName);
  ana.doAnalysis();

  return;
}

int main(int argc, char *argv[]){
  if(argc!=2){
    cout<<"Usage: parseBinaryFile [inputFilename]"<<endl;
    return 0;
  }
  std::string inputFileName = argv[1];
  std::cout << "inputFileName " << inputFileName << std::endl;

  //define ROOT application object
  gROOT->SetBatch(true);
  theApp = new TApplication("App", &argc, argv);
  parseBinaryFile(inputFileName); 

  //return 1;
  gSystem->Exit(0);
}
