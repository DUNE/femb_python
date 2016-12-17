//compile independently with: g++ -std=c++11 -o processNtuple_noiseMeasurement processNtuple_noiseMeasurement.cxx `root-config --cflags --glibs`
#include <iostream>
#include <fstream>
#include <sstream>
#include <cstdlib>
using namespace std;

#include "TROOT.h"
#include "TMath.h"
#include "TApplication.h"
#include "TFile.h"
#include "TTree.h"
#include "TH1.h"
#include "TH2.h"
#include "TString.h"
#include "TCanvas.h"
#include "TSystem.h"
#include "TGraph.h"
#include "TProfile2D.h"
#include "TF1.h"

using namespace std;

//global TApplication object declared here for simplicity
TApplication *theApp;

class Analyze {
	public:
	Analyze(std::string inputFileName);
        int processFileName(std::string inputFileName, std::string &baseFileName);
	void doAnalysis();
	void organizeData();
	void analyzeSubrun(unsigned int subrun);
	void analyzeChannel(unsigned int chan, const std::vector<unsigned short> &wf);
	void drawWf(unsigned int chan, const std::vector<unsigned short> &wf);

	//Files
	TFile* inputFile;
	TFile *gOut;

	//ROI tr_rawdata variables
	TTree *tr_rawdata;
	unsigned short subrunIn, chanIn;
	std::vector<unsigned short> *wfIn = 0;

	//Constants
	const int numChan = 128;// 35t
	const float SAMP_PERIOD = 0.5; //us
	const int numSubrun = 32;

	//data objects
	TCanvas* c0;
	TGraph *gCh;
        std::vector<unsigned short> wfAll[32][128];

	//histograms
	TH2F *hSampVsChan;
	TProfile *pSampVsChan;
	TH2F *hMeanVsChan;
	TProfile *pMeanVsChan;
	TH2F *hRmsVsChan;
	TProfile *pRmsVsChan;
	TProfile *pFracStuckVsChan;
	TProfile2D *pFFTVsChan;

	TH2F *hSampVsChan_subrun[32];
};

Analyze::Analyze(std::string inputFileName){

	//get input file
	if( inputFileName.empty() ){
		std::cout << "Error invalid file name" << std::endl;
		gSystem->Exit(0);
	}

	inputFile = new TFile(inputFileName.c_str());
	if (inputFile->IsZombie()) {
		std::cout << "Error opening input file" << std::endl;
		gSystem->Exit(0);
	}

	if( !inputFile ){
		std::cout << "Error opening input file" << std::endl;
		gSystem->Exit(0);
	}

	//initialize tr_rawdata branches
  	tr_rawdata = (TTree*) inputFile->Get("femb_wfdata");
  	if( !tr_rawdata ){
		std::cout << "Error opening input file tree" << std::endl;
		gSystem->Exit(0);
  	}
	tr_rawdata->SetBranchAddress("subrun", &subrunIn);
	tr_rawdata->SetBranchAddress("chan", &chanIn);
  	tr_rawdata->SetBranchAddress("wf", &wfIn);

	//make output file
  	std::string outputFileName;
	if( processFileName( inputFileName, outputFileName ) )
		outputFileName = "output_processNtuple_noiseMeasurement_" + outputFileName;
	else
		outputFileName = "output_processNtuple_noiseMeasurement.root";

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

	//make subrun specific objects
	for(unsigned int sr = 0 ; sr < numSubrun ; sr++){
		char name[200];
		memset(name,0,sizeof(char)*100 );
        	sprintf(name,"hSampVsChan_subrun%i",sr);
		hSampVsChan_subrun[sr] = new TH2F(name,"",numChan,0-0.5,numChan-0.5,4096,-0.5,4096-0.5);
	}
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
	//organize tree data by subrun
	std::cout << "Organizing data by subrun" << std::endl;
	organizeData();

	//analyze each subrun individually
	for(unsigned int sr = 0 ; sr < numSubrun ; sr++){
		std::cout << "Analyzing subrun " << sr << std::endl;
		analyzeSubrun(sr);
	}

	//do summary analyses
	std::cout << "Doing summary analysis" << std::endl;

  	//output histograms, data objects
 	gOut->Cd("");
  	hSampVsChan->Write();
	pSampVsChan->Write();
  	hMeanVsChan->Write();
	pMeanVsChan->Write();
  	hRmsVsChan->Write();
  	pRmsVsChan->Write();
	pFracStuckVsChan->Write();
	pFFTVsChan->Write();

	//write subrun specific objects
	for(unsigned int sr = 0 ; sr < numSubrun ; sr++)
		hSampVsChan_subrun[sr]->Write();
  	gOut->Close();
}

void Analyze::organizeData(){
	//loop over tr_rawdata entries
  	Long64_t nEntries(tr_rawdata->GetEntries());
	tr_rawdata->GetEntry(0);
	//loop over input waveforms, group waveforms by subrun
	for(Long64_t entry(0); entry<nEntries; ++entry) { 
		tr_rawdata->GetEntry(entry);

		//make sure channels and subrun values are ok
		if( subrunIn < 0 || subrunIn >= numSubrun ) continue;
		if( chanIn < 0 || chanIn >= numChan ) continue;
		
		for( unsigned int s = 0 ; s < wfIn->size() ; s++ )
			wfAll[subrunIn][chanIn].push_back( wfIn->at(s) );
  	}//entries
}

void Analyze::analyzeSubrun(unsigned int subrun){

	//reset plots
	hSampVsChan->Reset();
	pRmsVsChan->Reset();

	//loop over channels, update subrun specific plots
	for(unsigned int ch = 0 ; ch < numChan ; ch++){
		analyzeChannel(ch,wfAll[subrun][ch]);
		//drawWf(ch,wfAll[subrun][ch]);
	}

	//put result in subrun specific object
	for(unsigned int ch = 0 ; ch < hSampVsChan->GetNbinsX() ; ch++){
	for(unsigned int code = 0 ; code < hSampVsChan->GetNbinsY() ; code++){
		double value = hSampVsChan->GetBinContent(ch+1, code+1);
		hSampVsChan_subrun[subrun]->SetBinContent( ch + 1, code+1,value);
	}
	}
}


//draw waveform if wanted
void Analyze::drawWf(unsigned int chan, const std::vector<unsigned short> &wf){
	gCh->Set(0);
	for( int s = 0 ; s < wf.size() ; s++ )
		gCh->SetPoint(gCh->GetN() , gCh->GetN() , wf.at(s) );
	std::cout << "Channel " << chan << std::endl;
	
	c0->Clear();
	std::string title = "Channel " + to_string( chan );
	gCh->SetTitle( title.c_str() );
	gCh->GetXaxis()->SetTitle("Sample Number");
	gCh->GetYaxis()->SetTitle("Sample Value (ADC counts)");
	gCh->Draw("ALP");
	c0->Update();
	//char ct;
	//std::cin >> ct;
	usleep(1000);
}

void Analyze::analyzeChannel(unsigned int chan, const std::vector<unsigned short> &wf){
	if( wf.size() == 0 )
		return;

	//calculate mean
	double mean = 0;
	int count = 0;
	for( int s = 0 ; s < wf.size() ; s++ ){
		if( (wf.at(s) & 0x3F ) == 0x0 || (wf.at(s) & 0x3F ) == 0x3F ) continue;
		double value = wf.at(s);
		mean += value;
		count++;
	}
	if( count > 0 )
		mean = mean / (double) count;

	//calculate rms
	double rms = 0;
	count = 0;
	for( int s = 0 ; s < wf.size() ; s++ ){
		if( (wf.at(s) & 0x3F ) == 0x0 || (wf.at(s) & 0x3F ) == 0x3F ) continue;
		double value = wf.at(s);
		rms += (value-mean)*(value-mean);
		count++;
	}	
	if( count > 1 )
		rms = TMath::Sqrt( rms / (double)( count - 1 ) );
	
	//fill channel waveform hists
	for( int s = 0 ; s < wf.size() ; s++ ){
		unsigned short samp =  wf.at(s);
		hSampVsChan->Fill( chan, samp);

		//measure stuck code fraction
		if( (wf.at(s) & 0x3F ) == 0x0 || (wf.at(s) & 0x3F ) == 0x3F )
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
	for( int s = 0 ; s < wf.size() ; s++ ){
		if( (wf.at(s) & 0x3F ) == 0x0 || (wf.at(s) & 0x3F ) == 0x3F ) continue;
		gCh->SetPoint(gCh->GetN() , s , wf.at(s) );
	}

	//compute FFT - use TGraph to interpolate between missing samples
	//int numFftBins = wf.size();
	int numFftBins = 500;
	if( numFftBins > wf.size() )
		numFftBins = wf.size();
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
