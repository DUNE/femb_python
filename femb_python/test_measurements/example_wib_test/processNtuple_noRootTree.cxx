//compile independently with: g++ -std=c++11 -o processNtuple_noRootTree processNtuple_noRootTree.cxx `root-config --cflags --glibs`
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
	void parseAsicRawData(int asic);
	void analyzeChannel(unsigned int chan, std::vector<short> *wf);

	//Files
	ifstream infile;
	TFile *gOut;

	//Constants
	const int numChan = 128;// 35t

	//data objects
	TCanvas* c0;
	TGraph *gCh;
	std::vector<unsigned short> asicPackets[8];
	std::vector<short> wfIn[128];

	//histograms
	TH2F *hSampVsChan;
	TProfile *pSampVsChan;
	TH2F *hMeanVsChan;
	TProfile *pMeanVsChan;
	TH2F *hRmsVsChan;
	TProfile *pRmsVsChan;
	TProfile *pFracStuckVsChan;
	TProfile2D *pFFTVsChan;
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
  	std::string outputFileName;
	if( processFileName( inputFileName, outputFileName ) )
		outputFileName = "output_processNtuple_" + outputFileName + ".root";
	else
		outputFileName = "output_processNtuple.root";

  	gOut = new TFile(outputFileName.c_str() , "RECREATE");

  	//initialize canvas
  	c0 = new TCanvas("c0", "c0",1400,800);

	//initialize graphs
	gCh = new TGraph();

  	//output histograms, data objects
  	hSampVsChan = new TH2F("hSampVsChan","",numChan,0-0.5,numChan-0.5,4096,-0.5,4096-0.5);
 	pSampVsChan = new TProfile("pSampVsChan","",numChan,0-0.5,numChan-0.5);
  	hMeanVsChan = new TH2F("hMeanVsChan","",numChan,0-0.5,numChan-0.5,4096,-0.5,4096-0.5);
	pMeanVsChan = new TProfile("pMeanVsChan","",numChan,0-0.5,numChan-0.5);
  	hRmsVsChan = new TH2F("hRmsVsChan","",numChan,0-0.5,numChan-0.5,300,0,300.);
  	pRmsVsChan = new TProfile("pRmsVsChan","",numChan,0-0.5,numChan-0.5);
	pFracStuckVsChan = new TProfile("pFracStuckVsChan","",numChan,0-0.5,numChan-0.5);
	pFFTVsChan = new TProfile2D("pFFTVsChan","",numChan,0-0.5,numChan-0.5,100,0,1);
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

	for( unsigned int ch = 0 ; ch < 128 ; ch++ ){
		/*
		gCh->Set(0);
		for( int s = 0 ; s < wfIn[ch].size() ; s++ )
			gCh->SetPoint(gCh->GetN() , s , wfIn[ch].at(s) );
		c0->Clear();
		gCh->Draw("ALP");
		c0->Update();
		char ct;
		std::cin >> ct;
		*/
		analyzeChannel(ch, &wfIn[ch]);
	}

	c0->Clear();
	hSampVsChan->Draw("COLZ");
	c0->Update();
	usleep(100000);
	//char ct;
	//std::cin >> ct;

    	gOut->Cd("");
  	hSampVsChan->Write();
	pSampVsChan->Write();
  	hMeanVsChan->Write();
	pMeanVsChan->Write();
  	hRmsVsChan->Write();
  	pRmsVsChan->Write();
	pFracStuckVsChan->Write();
	pFFTVsChan->Write();
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
		if( packetSize < 6 )
			continue;

		//get ASIC number
		unsigned short asicNum = (unsigned short ) ntohs(buffer_ushort[basePos + 5]);
		//std::cout << "ASIC NUMBER " << asicNum << std::endl;
		if(  asicNum > 7 )
			continue;

		//get UDP packet number
		unsigned short packetNum = (unsigned short) ntohs(buffer_ushort[basePos + 7]);
		//std::cout << "PACKET NUMBER " << packetNum << std::endl;

		//store actual data in vector
		for( unsigned int line = basePos + 14 ; line <= endPos ;line++){
			unsigned short dataWord = (unsigned short) ntohs(buffer_ushort[line]);
			asicPackets[asicNum].push_back(dataWord);
			//std::cout << std::dec << line << "\t" << basePos << "\t" << endPos << "\t" << std::hex << dataWord << std::endl;
		}
	}//end loop over headers
		
    	delete[] buffer_ushort;
}

void Analyze::parseRawData(){
	//loop over ASIC data packets
	for(int asic = 0 ; asic < 8 ; asic++ )
		parseAsicRawData(asic);

	return;
}

void Analyze::parseAsicRawData(int asic){
	if( asicPackets[asic].size() == 0 )
		return;

	//find 0xface words
	std::vector<unsigned int> facePos;
	for( unsigned int line = 0 ; line < asicPackets[asic].size() ; line++){
		//std::cout << asicPackets[asic].at(line) << std::endl;
		if( asicPackets[asic].at(line) == 0xface )
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
	while(line < asicPackets[asic].size() ){

		//don't use clipped packets
		if( line + 13 >= asicPackets[asic].size() )
			break;

		unsigned short dataWord = asicPackets[asic].at(line);
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
			if( lineNum >= asicPackets[asic].size() ) continue;
			wordArray[wordNum] = asicPackets[asic].at(lineNum);
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

		//chSamp[2] = (wordArray[1] & 0xFFF0 ) >> 4; // nearly ok
		//chSamp[2] = ((wordArray[1] & 0x000F ) << 8) | ((wordArray[0] & 0xFF00 ) >> 8); //nearly ok	
		//chSamp[2] = ((wordArray[0] & 0x00FF ) << 4) | ((wordArray[3] & 0xF000 ) >> 12);	

		//std::cout << "PARSED SAMPLES " << std::endl;
		for(int ch = 0 ; ch < 16 ; ch++){
			//std::cout << asic << "\t" << ch << "\t" << std::hex << chSamp[ch] << "\t" << std::dec << chSamp[ch] << std::endl;
			int chNum = 16*asic + ch;
			if( chNum < 0 || chNum > 127 )
				continue;
			wfIn[chNum].push_back(chSamp[ch]);
		}
		//char ct;
		//std::cin >> ct;
	}//end loop over asic packets

	return;
}

void Analyze::analyzeChannel(unsigned int chan, std::vector<short> *wf){

	 //skip known bad channels here

	//calculate mean
	double mean = 0;
	int count = 0;
	for( int s = 0 ; s < wf->size() ; s++ ){
		if(  wf->at(s) < 10 ) continue;
		if( (wf->at(s) & 0x3F ) == 0x0 || (wf->at(s) & 0x3F ) == 0x3F ) continue;
		double value = wf->at(s);
		mean += value;
		count++;
	}
	if( count > 0 )
		mean = mean / (double) count;

	//calculate rms
	double rms = 0;
	count = 0;
	for( int s = 0 ; s < wf->size() ; s++ ){
		if(  wf->at(s) < 10 ) continue;
		if( (wf->at(s) & 0x3F ) == 0x0 || (wf->at(s) & 0x3F ) == 0x3F ) continue;
		double value = wf->at(s);
		rms += (value-mean)*(value-mean);
		count++;
	}	
	if( count > 1 )
		rms = TMath::Sqrt( rms / (double)( count - 1 ) );

	//fill channel waveform hists
	for( int s = 0 ; s < wf->size() ; s++ ){
		short samp =  wf->at(s);
		hSampVsChan->Fill( chan, samp);

		//measure stuck code fraction
		if( (wf->at(s) & 0x3F ) == 0x0 || (wf->at(s) & 0x3F ) == 0x3F )
			pFracStuckVsChan->Fill(chan, 1);
		else
			pFracStuckVsChan->Fill(chan, 0);
	}

	hMeanVsChan->Fill( chan, mean );
	pMeanVsChan->Fill( chan, mean );
	hRmsVsChan->Fill(chan, rms);
	pRmsVsChan->Fill(chan, rms);

	//load hits into TGraph, skip stuck codes
	gCh->Set(0);
	for( int s = 0 ; s < wf->size() ; s++ ){
		if(  wf->at(s) < 10 ) continue;
		if( (wf->at(s) & 0x3F ) == 0x0 || (wf->at(s) & 0x3F ) == 0x3F ) continue;
		gCh->SetPoint(gCh->GetN() , s , wf->at(s) );
	}
	if( gCh->GetN() == 0 )
		return;
	
	//compute FFT - use TGraph to interpolate between missing samples
	//int numFftBins = wf->size();
	int numFftBins = 500;
	if( numFftBins > wf->size() )
		numFftBins = wf->size();
	TH1F *hData = new TH1F("hData","",numFftBins,0,numFftBins);
	for( int s = 0 ; s < numFftBins ; s++ ){
		double adc = gCh->Eval(s);
		hData->SetBinContent(s+1,adc);
	}

	TH1F *hFftData = new TH1F("hFftData","",numFftBins,0,numFftBins);
    	hData->FFT(hFftData,"MAG");
    	for(int i = 1 ; i < hFftData->GetNbinsX() ; i++ ){
		double freq = 2.* i / (double) hFftData->GetNbinsX() ;
		pFFTVsChan->Fill( chan, freq,  hFftData->GetBinContent(i+1) );
	}

	//draw waveform if wanted
	if( 0 ){
		gCh->Set(0);
		for( int s = 0 ; s < wf->size() ; s++ )
			gCh->SetPoint(gCh->GetN() , gCh->GetN() , wf->at(s) );
		std::cout << "Channel " << chan << std::endl;
		c0->Clear();
		
		std::string title = "Channel " + to_string( chan );
		gCh->SetTitle( title.c_str() );
		gCh->GetXaxis()->SetTitle("Sample Number");
		gCh->GetYaxis()->SetTitle("Sample Value (ADC counts)");
		//gCh->GetXaxis()->SetRangeUser(0,128);
		//gCh->GetXaxis()->SetRangeUser(0,num);
		//gCh->GetYaxis()->SetRangeUser(500,1000);
		gCh->Draw("ALP");
		/*
		c0->Divide(2);
		c0->cd(1);
		hData->Draw();
		c0->cd(2);
		hFftData->SetBinContent(1,0);
		hFftData->GetXaxis()->SetRangeUser(0, hFftData->GetNbinsX()/2. );
		hFftData->Draw();
		*/
		c0->Update();
		//char ct;
		//std::cin >> ct;
		usleep(1000);
	}

	delete hData;
	delete hFftData;
}

void processNtuple(std::string inputFileName) {

  Analyze ana(inputFileName);
  ana.doAnalysis();

  return;
}

int main(int argc, char *argv[]){
  if(argc!=2){
    cout<<"Usage: processNtuple [inputFilename]"<<endl;
    return 0;
  }

  std::string inputFileName = argv[1];
  std::cout << "inputFileName " << inputFileName << std::endl;

  //define ROOT application object
  theApp = new TApplication("App", &argc, argv);
  processNtuple(inputFileName); 

  //return 1;
  gSystem->Exit(0);
}
