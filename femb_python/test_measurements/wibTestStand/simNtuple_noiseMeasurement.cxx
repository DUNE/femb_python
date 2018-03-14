//compile independently with: g++ -std=c++11 -o simNtuple_noiseMeasurement simNtuple_noiseMeasurement.cxx `root-config --cflags --glibs`
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
#include "TRandom3.h"

using namespace std;

//global TApplication object declared here for simplicity
TApplication *theApp;

class Analyze {
	public:
	Analyze();
	void doAnalysis();
	void simNoise();
	void drawWf(unsigned int subrun, unsigned int chan);

	//Files
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
	std::vector<unsigned short> wfIn[1024][128]; //subrun, ch
	TRandom3 *r;

	//histograms

	//output tree and variable
	unsigned short fSubrun, fChan;
	std::vector<unsigned short> fWf;
	TTree *tTree;
};

Analyze::Analyze(){

	//make output file
  	std::string outputFileName = "output_simNtuple_noiseMeasurement.root";

  	gOut = new TFile(outputFileName.c_str() , "RECREATE");

  	//initialize canvas
  	c0 = new TCanvas("c0", "c0",1400,800);

	//initialize graphs
	gCh = new TGraph();

	r = new TRandom3(0);

	//output tree
	tTree = new TTree("femb_wfdata","femb_wfdata");
	tTree->Branch("subrun", &fSubrun, "subrun/s");
  	tTree->Branch("chan", &fChan, "chan/s");
	tTree->Branch("wf", "vector<unsigned short>", &fWf);
}

void Analyze::doAnalysis(){

	//simulate noise measurements
	simNoise();

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

void Analyze::simNoise(){

	//double rms = 10.;
	double pedestalBase = 700.;
	int numSamples = 2900;

	for(unsigned int subrun = 0 ; subrun < 32 ; subrun++ ){
		double rms = subrun/8*5 + 5;
		std::cout << "Simulating subrun " << subrun << std::endl;
		for( unsigned int ch = 0 ; ch <maxNumChan ; ch++ ){
			double pedestal = pedestalBase + 100.*r->Rndm();
			//std::cout << "subrun " << subrun << "\tch " << ch << "\tped " << pedestal << std::endl;
			for( unsigned int s = 0 ; s < numSamples ; s++ ){
				double sampVal = r->Gaus(pedestal, rms);
				wfIn[subrun][ch].push_back( (unsigned short) sampVal );
			}
		}
		maxSubrunParsed = subrun;
	}
}

void Analyze::drawWf(unsigned int subrun, unsigned int chan){
	gCh->Set(0);
	for( int s = 0 ; s < wfIn[subrun][chan].size() ; s++ )
		gCh->SetPoint(gCh->GetN() , s , wfIn[subrun][chan].at(s) );
	c0->Clear();
	gCh->Draw("ALP");
	c0->Update();
	usleep(100000);
	char ct;
	std::cin >> ct;

	return;
}

void simNtuple_gainMeasurement() {

  Analyze ana;
  ana.doAnalysis();

  return;
}

int main(int argc, char *argv[]){
  //define ROOT application object
  gROOT->SetBatch(true);
  theApp = new TApplication("App", &argc, argv);
  simNtuple_gainMeasurement(); 

  //return 1;
  gSystem->Exit(0);
}
