//compile independently with: g++ -std=c++11 -o processNtuple_simpleMeasurement processNtuple_simpleMeasurement.cxx `root-config --cflags --glibs`
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
#include "TImage.h"

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

	//Files
	TFile* inputFile;
	TFile *gOut;

	//ROI tr_rawdata variables
	TTree *tr_rawdata;
	unsigned short subrunIn, chanIn;
	std::vector<unsigned short> *wfIn = 0;

	//Constants
	const int numChan = 16;
	const float SAMP_PERIOD = 0.5; //us
	const int numSubrun = 1;

	//data objects
	TCanvas* c0;
	TGraph *gCh;
        std::vector<unsigned short> wfAll[1][16];

	//histograms
	TGraph *gAll[16];
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
  	std::string outputFileName = "output_processNtuple_funcgenMeasurement.root";
	//if( processFileName( inputFileName, outputFileName ) )
	//	outputFileName = "output_processNtuple_simpleMeasurement_" + outputFileName;

  	gOut = new TFile(outputFileName.c_str() , "RECREATE");

  	//initialize canvas
  	c0 = new TCanvas("c0", "c0",1400,800);

	//initialize graphs
	gCh = new TGraph();

  	//output histograms, data objects
  	for(unsigned int ch = 0 ; ch < numChan ; ch++){
		gAll[ch] = new TGraph();
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
	//for(unsigned int sr = 0 ; sr < numSubrun ; sr++){
	//	std::cout << "Analyzing subrun " << sr << std::endl;
	//	analyzeSubrun(sr);
	//}
        analyzeSubrun(0);

	//do summary analyses
	std::cout << "Doing summary analysis" << std::endl;

        c0->Clear();
 
        gAll[0]->Draw("ALP");
        gAll[0]->SetTitle("Long Ramp Data - 16 Channels");
        gAll[0]->GetXaxis()->SetTitle("Sample Number");
        gAll[0]->GetYaxis()->SetTitle("Sample Value (ADC count)");
        for(unsigned int ch = 1 ; ch < numChan ; ch++)
        	gAll[ch]->Draw("LP");
	c0->Update();

	TImage *img = TImage::Create();
	img->FromPad(c0);
  	std::stringstream imgstream;
	imgstream << "summaryPlot_funcgenMeasurement.png";
	std::string imgstring( imgstream.str() );
  	img->WriteImage(imgstring.c_str());

  	//output histograms, data objects
 	gOut->Cd("");
	c0->Write("summaryPlot");
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
	//loop over channels, update subrun specific plots
	for(unsigned int ch = 0 ; ch < numChan ; ch++){
		analyzeChannel(ch,wfAll[subrun][ch]);
	}
}

void Analyze::analyzeChannel(unsigned int chan, const std::vector<unsigned short> &wf){
	if( wf.size() == 0 )
		return;
        if( chan >= numChan )
		return;

	//load hits into TGraph, skip stuck codes
	gAll[chan]->Set(0);
	for( int s = 0 ; s < wf.size() ; s++ ){
		gAll[chan]->SetPoint(gAll[chan]->GetN() , s , wf.at(s) );
	}
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
  gROOT->SetBatch(true);
  theApp = new TApplication("App", &argc, argv);
  processNtuple(inputFileName); 

  //return 1;
  gSystem->Exit(0);
}
