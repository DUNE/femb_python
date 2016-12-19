//compile independently with: g++ -std=c++11 -o summaryAnalysis_noiseMeasurement summaryAnalysis_noiseMeasurement.cxx `root-config --cflags --glibs`
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
#include "TGraphErrors.h"
#include "TProfile2D.h"
#include "TF1.h"
#include "TLegend.h"
#include "TImage.h"

using namespace std;

//global TApplication object declared here for simplicity
TApplication *theApp;

class Analyze {
	public:
	Analyze(std::string fileName);
	int processFileName(std::string inputFileName, std::string &baseFileName);
	void doAnalysis();
	void analyzeSubrun(unsigned int subrun);
	void outputResults();

	std::string inputFileName;
	std::string outputFileName;
	TFile *inputFile;
	TFile *gOut;

	//Constants
	const int maxNumChan = 128;// 35t
	const int numGain = 4;
	const int numShape = 4;
	const int numBase = 2;
	const int numSubrun = 32;

	//Data objects
	TCanvas* c0;
	TGraphErrors *gCh;
	double rmsMeasurement[4][4][2][128];

	//Output histograms
	TH1F *hRmsVsChan[4][4][2];

	unsigned int gain[32] = {0,0,0,0,0,0,0,0,  1,1,1,1,1,1,1,1, 2,2,2,2,2,2,2,2, 3,3,3,3,3,3,3,3};
	unsigned int shape[32] = {0,0,1,1,2,2,3,3,  0,0,1,1,2,2,3,3, 0,0,1,1,2,2,3,3, 0,0,1,1,2,2,3,3};
	unsigned int base[32] = {0,1,0,1,0,1,0,1,  0,1,0,1,0,1,0,1, 0,1,0,1,0,1,0,1, 0,1,0,1,0,1,0,1};
};

Analyze::Analyze(std::string fileName){

	inputFileName = fileName;

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

	//make output file
  	outputFileName = "output_summaryAnalysis_noiseMeasurement.root";
	//if( processFileName( inputFileName, outputFileName ) )
	//	outputFileName = "output_summaryAnalysis_noiseMeasurement_" + outputFileName + ".root";
  	gOut = new TFile(outputFileName.c_str() , "RECREATE");

  	//initialize canvas
  	c0 = new TCanvas("c0", "c0",1600,850);

	//initialize graphs
	gCh = new TGraphErrors();

	//initialize noise measurement array
	for(int g = 0 ; g < numGain ; g++ )
	for(int s = 0 ; s < numShape ; s++ )
	for(int b = 0 ; b < numBase ; b++ )
	for(int c = 0 ; c < maxNumChan ; c++ ){
		rmsMeasurement[g][s][b][c] = -1;
	}

	for(int g = 0 ; g < numGain ; g++ )
	for(int s = 0 ; s < numShape ; s++ )
	for(int b = 0 ; b < numBase ; b++ ){
		char name[200];
		memset(name,0,sizeof(char)*100 );
        	sprintf(name,"hRmsVsChan_%i_%i_%i",g,s,b);
		hRmsVsChan[g][s][b] = new TH1F(name,"",128,0-0.5,128-0.5);
	}
}

int Analyze::processFileName(std::string inputFileName, std::string &baseFileName){
        //check if filename is empty
        if( inputFileName.size() == 0 ){
                std::cout << "summaryAnalysis - processFileName : Invalid filename " << std::endl;
                return 0;
        }

        //remove path from name
        size_t pos = 0;
        std::string delimiter = "/";
        while ((pos = inputFileName.find(delimiter)) != std::string::npos)
                inputFileName.erase(0, pos + delimiter.length());

	if( inputFileName.size() == 0 ){
                std::cout << "summaryAnalysis -processFileName : Invalid filename " << std::endl;
                return 0;
        }

        //replace / with _
        std::replace( inputFileName.begin(), inputFileName.end(), '/', '_'); // replace all 'x' to 'y'
        std::replace( inputFileName.begin(), inputFileName.end(), '-', '_'); // replace all 'x' to 'y'

	baseFileName = inputFileName;
	
	return 1;
}

void Analyze::doAnalysis(){
	//loop over subruns
	for(unsigned int subrun = 0 ; subrun < numSubrun ; subrun++ ){
		std::cout << "Analyzing subrun " << subrun << std::endl;
		analyzeSubrun(subrun );
	}
}

void Analyze::analyzeSubrun(unsigned int subrun ){

	if(subrun >= numSubrun )
		return;

	char name[200];
	memset(name,0,sizeof(char)*100 );
        sprintf(name,"hSampVsChan_subrun%i",subrun);
	
	//sample vs chan histogram
	TH2F *h1 = (TH2F*)inputFile->Get( name );
	if( !h1 ){
  		std::cout << "summaryAnalysis - doAnalysis - Could not find requested histogram, exiting" << std::endl;
		gSystem->Exit(0);
  	}

	//look at hists
	if(0){
		c0->Clear();
		h1->Draw("COLZ");
		c0->Update();
		usleep(100000);
		//char cf;
		//std::cin >> cf;
	}

	//make corrected channel histogram
	TH1D *hAdcNoStuck = new TH1D("hAdcNoStuck","",4096,0-0.5,4096-0.5);
	
	//loop through channels 
	for(int ch = 0 ; ch < maxNumChan ; ch++ ){
		TH2F *h = h1;
		//check that histogram has correct number of channels
		int numCh = h->GetNbinsX();

		//get slice for channel
		char name[200];
		memset(name,0,sizeof(char)*100 );
        	sprintf(name,"hChan_%.3i",ch);
		TH1D *hChan = h->ProjectionY(name,ch+1,ch+1);
		if( hChan->GetEntries() < 10 )
			continue;

		//skip known bad cannels

		//at this point have necessary channel data, do channel analysis

		//find mean and RMS of raw sample distribution
		hChan->GetXaxis()->SetRangeUser(1,4094);
		double meanSampVal = hChan->GetMean();
		double maxSampVal = hChan->GetBinCenter( hChan->GetMaximumBin() ) ;
		double rmsVal = hChan->GetRMS();
		if( rmsVal < 10 ) // get this when all samples in same bin
			rmsVal = 10;
		double minVal = maxSampVal - 10*rmsVal;
		if( minVal < 1 )
			minVal = 1;
		double maxVal = maxSampVal + 10*rmsVal;
		if( maxVal > 4094 )
			maxVal = 4094;
		hChan->GetXaxis()->SetRangeUser(minVal,maxVal);
		//hChan->GetXaxis()->SetRangeUser(maxSampVal - 100,maxSampVal + 100);
		double maxSampValRms = hChan->GetRMS();

		//measure stuck codes, get stuck code free distribution
		int numCode = 0;
		int numStuck = 0;
		hAdcNoStuck->Reset();
		
		for( int s = 0 ; s < hChan->GetNbinsX() ; s++ ){
			int numSamp = hChan->GetBinContent(s+1);
			numCode = numCode + numSamp;
			int adc = s;
			if( (s & 0x3F) == 0 ) numStuck = numStuck + numSamp;
			if( (s & 0x3F) == 1 ) numStuck = numStuck + numSamp;
			if( (s & 0x3F) == 0x3F ) numStuck = numStuck + numSamp;

			if( (s & 0x3F) == 0 || (s & 0x3F) == 1 || (s & 0x3F) == 0x3F )
				continue;
			hAdcNoStuck->SetBinContent(s+1,numSamp);
		}

		//find mean and RMS of sample distribution with stuck codes ommitted
		hAdcNoStuck->GetXaxis()->SetRangeUser(1,4094);
		double meanSampValNoStuck = hAdcNoStuck->GetMean();
		double maxSampValNoStuck = hAdcNoStuck->GetBinCenter( hAdcNoStuck->GetMaximumBin() ) ;
		double rmsValNoStuck = hAdcNoStuck->GetRMS();
		if( rmsValNoStuck < 10 ) // get this when all samples in same bin
			rmsValNoStuck = 10;
		double minValNoStuck = maxSampValNoStuck - 10*rmsValNoStuck;
		if( minValNoStuck < 1 )
			minValNoStuck = 1;
		double maxValNoStuck = maxSampValNoStuck + 10*rmsValNoStuck;
		if( maxValNoStuck > 4094 )
			maxValNoStuck = 4094;
		hAdcNoStuck->GetXaxis()->SetRangeUser(minValNoStuck,maxValNoStuck);
		//hAdcNoStuck->GetXaxis()->SetRangeUser(maxSampValNoStuck - 100,maxSampValNoStuck + 100);
		double maxSampValRmsNoStuck = hAdcNoStuck->GetRMS();

		//record THE noise measurement into an array
		unsigned int srGain = gain[subrun];
		unsigned int srShape = shape[subrun];
		unsigned int srBase = base[subrun];
		if( srGain >=0 && srGain < 4 && srShape >= 0 && srShape < 4 && srBase >= 0 && srBase < 2 && ch >= 0 && ch < 128 ){
			rmsMeasurement[srGain][srShape][srBase][ch] = maxSampValRmsNoStuck;
			hRmsVsChan[srGain][srShape][srBase]->SetBinContent(ch+1, maxSampValRmsNoStuck);
		}

		continue;

		if(0){
			c0->Clear();
			//hChan->Draw();
			hAdcNoStuck->SetLineColor(kRed);
			hAdcNoStuck->Draw();
			c0->Update();
			//char cf;
			//std::cin >> cf;
		}
	} //end loop over channels

	delete hAdcNoStuck;
}

void Analyze::outputResults(){

	std::string gainArray[4] = {"4.7","7.8","14","25"};
	std::string baseArray[2] = {"200","900"};
	
	c0->Clear();
	c0->Divide(4,2);
	for(int b = 0 ; b < numBase ; b++ )
	//for(int s = 0 ; s < numShape ; s++ ){
	for(int g = 0 ; g < numGain ; g++ ){
		//int padNum = b*4 + s + 1;
		int padNum = b*4 + g + 1;
		c0->cd(padNum);
		/*
		hRmsVsChan[0][s][b]->GetYaxis()->SetRangeUser(0,20);
		hRmsVsChan[0][s][b]->Draw();
		hRmsVsChan[1][s][b]->Draw("same");
		hRmsVsChan[2][s][b]->Draw("same");
		hRmsVsChan[3][s][b]->Draw("same");
		*/
		std::string title = "Gain " + gainArray[g] + "mV/fC, Baseline " + baseArray[b] + "mV";
		hRmsVsChan[g][0][b]->SetTitle(title.c_str());
		hRmsVsChan[g][0][b]->GetXaxis()->SetTitle("FEMB Channel #");
		hRmsVsChan[g][0][b]->GetYaxis()->SetTitle("Channel RMS (ADC counts)");
		hRmsVsChan[g][0][b]->GetYaxis()->SetRangeUser(0,20);
		hRmsVsChan[g][0][b]->SetStats(kFALSE);
		hRmsVsChan[g][0][b]->SetLineColor(kBlack);
		hRmsVsChan[g][1][b]->SetLineColor(kBlue);
		hRmsVsChan[g][2][b]->SetLineColor(kGreen);
		hRmsVsChan[g][3][b]->SetLineColor(kRed);
		hRmsVsChan[g][0][b]->Draw();
		hRmsVsChan[g][1][b]->Draw("same");
		hRmsVsChan[g][2][b]->Draw("same");
		hRmsVsChan[g][3][b]->Draw("same");

		TLegend *leg = new TLegend(0.7,0.7,0.9,0.9);
   		leg->SetHeader("Shaping Time"); // option "C" allows to center the header
   		leg->AddEntry(hRmsVsChan[g][0][b],"0.5us","l");
		leg->AddEntry(hRmsVsChan[g][1][b],"1us","l");
		leg->AddEntry(hRmsVsChan[g][2][b],"2us","l");
		leg->AddEntry(hRmsVsChan[g][3][b],"3us","l");
   		leg->Draw();
	}
	c0->Update();

	//save summary plots
	TImage *img = TImage::Create();
	img->FromPad(c0);
  	std::stringstream imgstream;
	imgstream << "summaryPlot_noiseMeasurement.png";
	std::string imgstring( imgstream.str() );
  	img->WriteImage(imgstring.c_str());

	//write histograms to file
	gOut->cd("");
	c0->Write("c0_SummaryRmsVsChan");
	for(int g = 0 ; g < numGain ; g++ )
	for(int s = 0 ; s < numShape ; s++ )
	for(int b = 0 ; b < numBase ; b++ ){
		hRmsVsChan[g][s][b]->Write();
	}
  	gOut->Close();

	//write measurements to file
	/*
	ofstream outfile;
	std::stringstream outstream;
	//outstream << "output_fembTest_noiseMeasurement_constants_" << std::dec << metadata_date << std::hex << metadata_runidMSB << metadata_runidLSB << ".txt";
	outstream << "output_fembTest_noiseMeasurement_constants" << ".txt";
	std::string outstring( outstream.str() );
  	outfile.open (outstring, std::ofstream::out);
	for(int g = 0 ; g < numGain ; g++ )
	for(int s = 0 ; s < numShape ; s++ )
	for(int b = 0 ; b < numBase ; b++ )
	for(int c = 0 ; c < maxNumChan ; c++ ){
		outfile << g << "\t" << s << "\t" << b << "\t" << c << "\t" << rmsMeasurement[g][s][b][c] << std::endl;
	}
  	outfile.close();
	*/
}

void summaryAnalysis_doFembTest_noiseMeasurement(std::string inputFileName) {
  //Initialize analysis class
  Analyze ana(inputFileName);
  //Run analysis
  ana.doAnalysis();
  //Output results
  ana.outputResults();
  return;
}

int main(int argc, char *argv[]){
  if(argc!=2){
    cout<<"Usage: summaryAnalysis_doFembTest_noiseMeasurement [inputFilename]"<<endl;
    return 0;
  }

  std::string inputFileName = argv[1];
  std::cout << "inputFileName " << inputFileName << std::endl;

  //define ROOT application object
  theApp = new TApplication("App", &argc, argv);
  summaryAnalysis_doFembTest_noiseMeasurement(inputFileName); 

  //return 1;
  gSystem->Exit(0); //required by ROOT
}
