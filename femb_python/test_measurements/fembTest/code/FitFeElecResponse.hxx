#include <iostream>
#include <stdlib.h>
#include <math.h>
#include "TMinuit.h"

///////////RESPONSE CLASS/////////////////

class FeElecResponse {
private:

public:
  FeElecResponse();
  ~FeElecResponse();
  void getSignalValue(double time, double base, double pulseStart, double shapeTime, double amp,double& simVal);
  void getSignalValueFromVector(double time, double base, double pulseStart, double shapeTime, double amp,double& simVal);
  void responseFunc( double time, double To, double Ao, double& val);
  std::vector<double> sig;
  unsigned int sigNum;
  double sigPeriod;
};

FeElecResponse::FeElecResponse(){
  //load response function into vector, use to interpolate
  sigNum = 5000;
  sigPeriod = 1./500.;
  for(unsigned int i = 0 ; i < sigNum ; i++){
    double time = i*sigPeriod;
    double val = 0;
    getSignalValue(time, 0., 0., 1., 1., val); //"unit" response, base = 0, start = 0, shape = 1, amp = 1
    sig.push_back(val);
  }
}

FeElecResponse::~FeElecResponse(){
}

//function to get response function value from response function
void FeElecResponse::getSignalValue(double time, double base, double pulseStart, double shapeTime, double amp,double& simVal){
  double pulseTime = 0;
  if( time > pulseStart )
  	pulseTime = time - pulseStart;
  simVal  = 0;
  responseFunc( pulseTime, shapeTime, amp, simVal);
  simVal += base;
  return;
}

//get response function value quickly from vector interpolation
void FeElecResponse::getSignalValueFromVector(double time, double base, double pulseStart, double shapeTime, double amp,double& simVal){
  double pulseTime = 0;
  if( time > pulseStart )
    pulseTime = time - pulseStart;
  simVal = base;
  if( shapeTime <= 0 )
    return;

  //determine position of time value in signal vector
  double pulseTimeSamp = pulseTime/shapeTime/sigPeriod;
  unsigned int pulseSamp = floor(pulseTimeSamp);
  if( pulseSamp >= sigNum - 1 )
    return;
  
  //do linear interpolation
  double sigVal = sig[pulseSamp] + ( sig[pulseSamp+1] - sig[pulseSamp] )*(pulseTimeSamp - pulseSamp);
  //scale by amplitude factor
  sigVal = amp*sigVal;
  simVal += sigVal;
  return;
}

//FE ASIC response
void FeElecResponse::responseFunc( double time, double To, double Ao, double& val){
  val = 4.31054*exp(-2.94809*time/To)*Ao - 2.6202*exp(-2.82833*time/To)*cos(1.19361*time/To)*Ao
  -2.6202*exp(-2.82833*time/To)*cos(1.19361*time/To)*cos(2.38722*time/To)*Ao
  +0.464924*exp(-2.40318*time/To)*cos(2.5928*time/To)*Ao
  +0.464924*exp(-2.40318*time/To)*cos(2.5928*time/To)*cos(5.18561*time/To)*Ao
  +0.762456*exp(-2.82833*time/To)*sin(1.19361*time/To)*Ao
  -0.762456*exp(-2.82833*time/To)*cos(2.38722*time/To)*sin(1.19361*time/To)*Ao
  +0.762456*exp(-2.82833*time/To)*cos(1.19361*time/To)*sin(2.38722*time/To)*Ao
  -2.6202*exp(-2.82833*time/To)*sin(1.19361*time/To)*sin(2.38722*time/To)*Ao
  -0.327684*exp(-2.40318*time/To)*sin(2.5928*time/To)*Ao
  +0.327684*exp(-2.40318*time/To)*cos(5.18561*time/To)*sin(2.5928*time/To)*Ao
  -0.327684*exp(-2.40318*time/To)*cos(2.5928*time/To)*sin(5.18561*time/To)*Ao
  +0.464924*exp(-2.40318*time/To)*sin(2.5928*time/To)*sin(5.18561*time/To)*Ao;
}

///////////STRUCTS FOR PULSE AND FIT CLASS/////////////////
struct FitFeElecResponse_Pulses{
  unsigned short num;
  float startSample;
  unsigned short firstSample;
  std::vector<unsigned short> wf;
  std::vector<bool> wfQuality;
};

struct FitFeElecResponse_Events{
  unsigned int eventNumber;
  float eventSample;
  std::vector<int> pulseSamples;
  std::vector<unsigned short> wf;
  std::vector<FitFeElecResponse_Pulses> pulseData;
};

///////////FIT CLASS/////////////////

//Stupid TMinuit global variables/functions
static void ffer_fitFuncML(int& npar, double* gout, double& result, double par[], int flg);
void ffer_calcLnL(double par[], double& result);
double ffer_sampleErr;
FeElecResponse *ffer_sig;
std::vector<FitFeElecResponse_Events> *ffer_eventData;

class FitFeElecResponse_multiPulse {
private:

public:

  FitFeElecResponse_multiPulse();
  ~FitFeElecResponse_multiPulse();

  void clearData();
  void addPulseData(unsigned int event, float eventSample, unsigned short num, float startSample, unsigned short firstSample, 
               const std::vector<unsigned short>& wf, const std::vector<bool>& wfQuality);
  void doFit(double initAmp, double initShape, double initBase, double initPeriod, double initOffset);
  void setSampleError(double err);

  bool showOutput;
  double sampleErr;
  unsigned int numPulses;
  double minLnL;
  bool fixStartSamples;
  int status;
  FeElecResponse *sig;
  std::vector<FitFeElecResponse_Events> fitEventData;
  std::vector<double> fitVals;
  std::vector<double> fitValErrs;
  std::vector<unsigned int> fixFitVars;
};

using namespace std;

FitFeElecResponse_multiPulse::FitFeElecResponse_multiPulse(){
  sig = new FeElecResponse();
  //initial values
  showOutput = 0;
  sampleErr = 1.;
  minLnL = 0;
  fixStartSamples = 1;
  status = -1;
  numPulses = 0;
}

FitFeElecResponse_multiPulse::~FitFeElecResponse_multiPulse(){
  delete sig;
}

void FitFeElecResponse_multiPulse::clearData(){
  numPulses = 0;
  fitEventData.clear();
  fitVals.clear();
  fitValErrs.clear();
  fixFitVars.clear();
}

void FitFeElecResponse_multiPulse::setSampleError(double err){
  sampleErr = 1.;
  if(err > 0.1 )
    sampleErr = err;
  return;
}

void FitFeElecResponse_multiPulse::addPulseData(unsigned int event, float eventSample, unsigned short num, float startSample, unsigned short firstSample, 
               const std::vector<unsigned short>& wf, const std::vector<bool>& wfQuality){
  if( fitEventData.size() == 0 ){
    FitFeElecResponse_Events evTemp;
    evTemp.eventNumber = event;
    evTemp.eventSample = eventSample;
    fitEventData.push_back( evTemp );
  }
  else if( event != fitEventData.back().eventNumber ){
    FitFeElecResponse_Events evTemp;
    evTemp.eventNumber = event;
    evTemp.eventSample = eventSample;
    fitEventData.push_back( evTemp );
  }
	
  FitFeElecResponse_Pulses pTemp;
  pTemp.num = num;
  pTemp.startSample = startSample;
  pTemp.firstSample = firstSample;
  pTemp.wf = wf;
  pTemp.wfQuality = wfQuality;
  fitEventData.back().pulseData.push_back(pTemp);
  numPulses++;
  return;
}

//wrapper function for TMinuit
void FitFeElecResponse_multiPulse::doFit(double initAmp, double initShape, double initBase, double initPeriod, double initOffset){
  if( numPulses == 0 )
    return;

  //give the global variables to the class objects (very lame)
  ffer_sampleErr = sampleErr;
  ffer_eventData = &fitEventData;
  ffer_sig = sig;

  //test to see if there are data point
  status = -1;

  //unsigned int numParameters = 4 + eventData.size();
  unsigned int numParameters = 5 + fitEventData.size();
  //std::unique_ptr<TMinuit> minimizer (new TMinuit(numParameters) );
  TMinuit *minimizer = new TMinuit(numParameters);

  //Set print level , -1 = suppress, 0 = info
  minimizer->SetPrintLevel(-1);
  if( showOutput == 1 )
    minimizer->SetPrintLevel(3);

  //define parameters
  minimizer->SetFCN(ffer_fitFuncML);
  minimizer->DefineParameter(0, "Amp", initAmp, abs(initAmp/1000.),0,0);
  minimizer->DefineParameter(1, "Shape", initShape, initShape/1000.,0,0);
  minimizer->DefineParameter(2, "Base", initBase, abs(initBase/1000.),0,0);
  minimizer->DefineParameter(3, "Period", initPeriod, 0.01,0,0);
  minimizer->DefineParameter(4, "Offset", initOffset, 0.01,0,0);

  //event start fit
  for(unsigned int ev = 0 ; ev < fitEventData.size() ; ev++ ){
    char name[200];
    memset(name,0,sizeof(char)*100 );
    sprintf(name,"Start_%i",ev);
    minimizer->DefineParameter(5+ev, name, fitEventData.at(ev).eventSample, 0.01,0,0);
  }

  //fix period variable if only one pulse
  if( numPulses == 1 ){
    minimizer->FixParameter(3);
  }

  //optionally fix parameters
  for( unsigned int i = 0 ; i <  fixFitVars.size() ; i++ ){
    if( fixFitVars.at(i) < numParameters )
      minimizer->FixParameter( fixFitVars.at(i) );
  }

  //fix all pulse start times, alternatively 
  if( fixStartSamples == 1){
    for(unsigned int ev = 0 ; ev < fitEventData.size() ; ev++ )
      minimizer->FixParameter(5+ev);
  }
  else
    minimizer->FixParameter(4);

  //Set Minuit flags
  Double_t arglist[10];
  arglist[0] = 0.5;
  Int_t ierflg = 0;
  minimizer->mnexcm("SET ERR", arglist ,1,ierflg);  //command, arguments, # arguments, error flag
        
  //MIGRAD minimization
  Double_t tmp[1];
  tmp[0] = 100000;
  Int_t err;
  minimizer->mnexcm("MIG", tmp ,1,err);
  status = err;
  
  fitVals.clear();
  fitValErrs.clear();
  for(unsigned int i = 0 ; i < numParameters ; i++ ){
    double fitVal, fitValErr;
    minimizer->GetParameter(i, fitVal, fitValErr);
    fitVals.push_back( fitVal );
    fitValErrs.push_back( fitValErr );
  }

  delete minimizer; //memory leak?

  return;
}

//likelihood calc - note not included in class
void calcLnL(double par[], double& result){
  double diffSq = 0;
  double dataX,fitY;
  unsigned short dataY;

  double norm = 1./(ffer_sampleErr)/(ffer_sampleErr);
  double amp = par[0];
  double shape = par[1];
  double base = par[2];

  //loop over events, pulses, samples
  for(unsigned int ev = 0 ; ev < ffer_eventData->size() ; ev++ ){
    for(unsigned int p = 0 ; p < ffer_eventData->operator[](ev).pulseData.size() ; p ++ ){
      double start = par[3]*ffer_eventData->operator[](ev).pulseData[p].num + par[5+ev] + par[4]; //proposed pulse start sample
      for(unsigned int s = 0 ; s < ffer_eventData->operator[](ev).pulseData[p].wf.size() ; s++ ){ //using data vector directly
        dataX = ffer_eventData->operator[](ev).pulseData[p].firstSample + s;
	
        //only allow fit to include certain part of pulse waveform
        if( ffer_eventData->operator[](ev).pulseData[p].wfQuality[s] == 0 )
          continue;
        dataY = ffer_eventData->operator[](ev).pulseData[p].wf[s];

        //void getSignalValueFromVector(double time, double base, double pulseStart, double shapeTime, double amp,double& simVal);
        ffer_sig->getSignalValueFromVector(dataX, base, start, shape, amp,fitY);
        diffSq = diffSq + (dataY - fitY)*(dataY - fitY)*norm; //gauss err assumed, noise is correlated but assume small
      }//end of sample loop
    }//end of pulse loop
  }//end of event loop

  //calculate value to minimize
  result = -0.5*diffSq;
  return;
}

//Fit wrapper function - used by Minuit - has to be static void, annoying
static void ffer_fitFuncML(int& npar, double* gout, double& result, double par[], int flg){
  calcLnL(par, result);
  result = -1.*result;//Minuit is minimizing result ie maximizing LnL
  return;
}

///////////PULSE ANALYSIS CLASS/////////////////

class FitFeElecResponse_analyzePulses {
private:

public:

  FitFeElecResponse_analyzePulses();
  ~FitFeElecResponse_analyzePulses();

  double constant_ampToHeightFactor = 0.0988165;
  const int const_preRange = 15;
  const int const_postRange = 25;
  const int const_maxCode = 4000;
  const float const_minPulseHeightForFit = 100;
  const float const_maxPulseHeightForFit = 3000;

  void clearData();
  void measureNoise(const std::vector<unsigned short> &wf);
  bool isGoodCode( unsigned short adcCode );
  bool calculateGoodCodeFraction( const std::vector<unsigned short> &wf );
  bool calculateMean( const std::vector<unsigned short> &wf );
  bool calculateRawRms( const std::vector<unsigned short> &wf, double mean );
  bool calculateRms( const std::vector<unsigned short> &wf, double mean );
  void addData(unsigned int event, const std::vector<int> &pulseSamples, const std::vector<unsigned short>& wf);
  void setBaseMeanRms(double mean, double rms);
  void analyzePulses();
  void analyzePulse(int startSampleNum, const std::vector<unsigned short> &wf, bool isNeg);
  void getPulseHeight( int startSampleNum, const std::vector<unsigned short> &wf, bool isNeg );
  void doPulseFit( int startSampleNum, const std::vector<unsigned short> &wf );

  std::vector<FitFeElecResponse_Events> eventData;
  FitFeElecResponse_multiPulse fitResponse;

  bool disable_isGoodCode = 0;
  double goodCodeFraction = 0;
  double baseMean = 0;
  double rawRms = 0;
  double baseRms = 0;
  double measuredPulseHeight = 0;
  bool enablePulseFits = 0;
  std::vector<double> pulseHeights;
  std::vector<double> fitPulseHeights;

  //initialize canvas
  //TCanvas *cTest;
  //TGraph *gChTest;
  //TGraph *gFitTest;
};

FitFeElecResponse_analyzePulses::FitFeElecResponse_analyzePulses(){
  //cTest = new TCanvas("cTest", "cTest",1400,800);
  //gChTest = new TGraph();
  //gFitTest = new TGraph();
}

FitFeElecResponse_analyzePulses::~FitFeElecResponse_analyzePulses(){
}

void FitFeElecResponse_analyzePulses::clearData(){
  eventData.clear();
  pulseHeights.clear();
  fitPulseHeights.clear();
}

void FitFeElecResponse_analyzePulses::setBaseMeanRms(double mean, double rms){
  baseMean = mean;
  baseRms = rms;
  if( rms < 0 )
    baseRms = 0;
}

void FitFeElecResponse_analyzePulses::addData(unsigned int event, const std::vector<int> &pulseSamples, const std::vector<unsigned short>& wf){
  if( eventData.size() == 0 ){
    FitFeElecResponse_Events evTemp;
    evTemp.eventNumber = event;
    evTemp.pulseSamples = pulseSamples;
    evTemp.wf = wf;
    eventData.push_back( evTemp );
  }
  else if( event != eventData.back().eventNumber ){
    FitFeElecResponse_Events evTemp;
    evTemp.eventNumber = event;
    evTemp.pulseSamples = pulseSamples;
    evTemp.wf = wf;
    eventData.push_back( evTemp );
  }
  return;
}

void FitFeElecResponse_analyzePulses::measureNoise( const std::vector<unsigned short> &wf){
  goodCodeFraction = 0;
  baseMean = -1;
  rawRms = -1;
  baseRms = -1;
  if( wf.size() == 0 )
    return;

  //calculate good sample fraction
  if( !calculateGoodCodeFraction( wf ) )
    return;

  //calculate mean
  if( !calculateMean( wf ) )
    return;

  //calculate rms  including stuck codes
  if( !calculateRawRms( wf , baseMean ) )
    return;

  //calculate rms without stuck codes
  if( !calculateRms( wf , baseMean ) )
    return;
}

bool FitFeElecResponse_analyzePulses::isGoodCode( unsigned short adcCode ){
  if( disable_isGoodCode == 1 ) return 1;
  if( (adcCode & 0x3F ) == 0x0 || (adcCode & 0x3F ) == 0x3F ) return 0;
  return 1;
}

bool FitFeElecResponse_analyzePulses::calculateGoodCodeFraction( const std::vector<unsigned short> &wf ){
  goodCodeFraction = 0;
  int totalCount = 0;
  int count = 0;
  for( int s = 0 ; s < wf.size() ; s++ ){
    totalCount++;
    if( isGoodCode( wf.at(s) ) ) 
	count++;
  }
  if( totalCount <= 0 )
    return 0;
  goodCodeFraction = (double)count / (double) totalCount;
  return 1;
}

bool FitFeElecResponse_analyzePulses::calculateMean( const std::vector<unsigned short> &wf ){
  baseMean = -1;
  double mean = 0;
  int count = 0;
  for( int s = 0 ; s < wf.size() ; s++ ){
    if( !isGoodCode( wf.at(s) ) ) continue;
    double value = wf.at(s);
    mean += value;
    count++;
  }
  if( count <= 0 )
    return 0;
  baseMean = mean / (double) count;
  return 1;
}

bool FitFeElecResponse_analyzePulses::calculateRawRms( const std::vector<unsigned short> &wf, double mean){
  rawRms = -1;
  double rms = 0;
  int count = 0;
  for( int s = 0 ; s < wf.size() ; s++ ){
    //if( checkCode == 1 && !isGoodCode( wf.at(s) ) ) continue;
    double value = wf.at(s);
    rms += (value-mean)*(value-mean);
    count++;
  }
  if( count <= 1 )
    return 0;
  if( rms <= 0 )
    return 0;	
  rawRms = TMath::Sqrt( rms / (double)( count - 1 ) );
  return 1;
}

bool FitFeElecResponse_analyzePulses::calculateRms( const std::vector<unsigned short> &wf, double mean){
  baseRms = -1;
  double rms = 0;
  int count = 0;
  for( int s = 0 ; s < wf.size() ; s++ ){
    if( !isGoodCode( wf.at(s) ) ) continue;
    double value = wf.at(s);
    rms += (value-mean)*(value-mean);
    count++;
  }
  if( count <= 1 )
    return 0;
  if( rms <= 0 )
    return 0;	
  baseRms = TMath::Sqrt( rms / (double)( count - 1 ) );
  return 1;
}

void FitFeElecResponse_analyzePulses::analyzePulses(){
  //measure rising pulse heights
  for(unsigned int ev = 0 ; ev < eventData.size() ; ev++ ){
    for( unsigned int p = 0 ; p < eventData.at(ev).pulseSamples.size() ; p++ ){
      //std::cout << eventData.at(ev).wf.size() << std::endl;
      if( p > 500 ) break; //hardcoded, bad!
      analyzePulse( eventData.at(ev).pulseSamples.at(p) , eventData.at(ev).wf , 0) ;
    }//end loop over pulses
  }//end loop over events
  //getAveragePulseHeight();
}

void FitFeElecResponse_analyzePulses::analyzePulse(int startSampleNum, const std::vector<unsigned short> &wf, bool isNeg){
  //require pulse is not beside waveform edge
  if( startSampleNum <= const_preRange || startSampleNum >= wf.size()  - const_postRange )
    return;
  if( const_preRange < 10 || const_postRange < 10 )
    return;
  if( wf.size() == 0 )
    return;
  //if( rmsSubrun0 <= 0 )
  //  return;

  //measure pulse height
  getPulseHeight(startSampleNum, wf, isNeg);

  //get pulse integral
  //getPulseIntegral(startSampleNum, wf);

  //do pulse fit
  if( enablePulseFits == 1 )
    doPulseFit(startSampleNum, wf);
}

void FitFeElecResponse_analyzePulses::getPulseHeight( int startSampleNum, const std::vector<unsigned short> &wf, bool isNeg ){
  measuredPulseHeight = -1;

  //calculate mean before pulse
  double mean = 0;
  int count = 0;
  for( int s = 0 ; s < startSampleNum-const_preRange ; s++ ){
    //if( !isGoodCode( wf.at(s) ) ) continue;
    double value = wf.at(s);
    mean += value;
    count++;
  }
  if( count <= 0 )
    return;
  mean = mean / (double) count;

  //find maximum sample value in pulse region
  int maxSampVal = -1;
  int maxSamp = -1;
  for(int s = startSampleNum-const_preRange ; s < startSampleNum + const_postRange ; s++){
    if( s < 0 ) continue;
    if( s >= wf.size() ) continue;
    //if( !isGoodCode( wf.at(s) ) ) continue;
    double value = wf.at(s);
    if( value > maxSampVal ){
      maxSampVal = value;
      maxSamp = s;
    }
  }
  if( maxSamp < 0 )
    return;

  //find maximum sample value in pulse region
  int minSampVal = const_maxCode + 1;
  int minSamp = -1;
  for(int s = startSampleNum-const_preRange ; s < startSampleNum + const_postRange ; s++){
    if( s < 0 ) continue;
    if( s >= wf.size() ) continue;
    //if( !isGoodCode( wf.at(s) ) ) continue;
    double value = wf.at(s);
    if( value < minSampVal ){
      minSampVal = value;
      minSamp = s;
    }
  }
  if( maxSamp < 0 || minSamp < 0)
    return;

  //
  if( minSampVal < mean - const_minPulseHeightForFit )
	return;

  //measure pulse height
  measuredPulseHeight = maxSampVal - baseMean;
  if( isNeg == 1 )
    measuredPulseHeight = minSampVal - baseMean;
  pulseHeights.push_back( measuredPulseHeight );

  //plot
  /*
  gChTest->Set(0);
  for(int s = startSampleNum-const_preRange ; s < startSampleNum + const_postRange ; s++){
    gChTest->SetPoint(gChTest->GetN() , s , wf.at(s) - baseMean );
  }

  
  if(0){
   //std::cout << mean << "\t" << baseMean << "\t" << minSamp - mean << std::endl;
   cTest->Clear();
   gChTest->SetMarkerStyle(21);
   gChTest->SetMarkerColor(kRed);
   gChTest->Draw("AP");
   cTest->Update();
   usleep(50000);
   //char ct;
   //std::cin >> ct;
  }
  */
}

void FitFeElecResponse_analyzePulses::doPulseFit( int startSampleNum, const std::vector<unsigned short> &wf ){
  if( measuredPulseHeight > const_maxPulseHeightForFit )
    return;
  if( measuredPulseHeight < const_minPulseHeightForFit )
    return;

  std::vector<unsigned short> wfData;
  std::vector<bool> wfDataQuality;
  bool isFirst = 1;
  unsigned int firstSample = -1;
  for(int s = startSampleNum-const_preRange ; s < startSampleNum + const_postRange ; s++){
    if( s < 0 ) continue;
    if( s >= wf.size() ) continue;
    if( !isGoodCode( wf.at(s) ) ) continue;
    if( isFirst == 1 ){
      firstSample = s;
      isFirst = 0;
    }
    wfData.push_back( wf.at(s) );
    wfDataQuality.push_back( 1 );
  }

  fitResponse.clearData();
  fitResponse.addPulseData(0, startSampleNum, 0, startSampleNum, firstSample, wfData, wfDataQuality);
  fitResponse.setSampleError( baseRms );
  fitResponse.showOutput = 0;
  fitResponse.fixStartSamples = 0;

  fitResponse.doFit( measuredPulseHeight/constant_ampToHeightFactor, 10, baseMean, 0, 0);
  fitPulseHeights.push_back( fitResponse.fitVals.at(0)*constant_ampToHeightFactor );
  
  /* //plot results
  double fitAmp = fitResponse.fitVals.at(0);
  double fitShape = fitResponse.fitVals.at(1);
  double fitBase = fitResponse.fitVals.at(2);
  double fitStart = fitResponse.fitVals.at(5);

  gChTest->Set(0);
  gFitTest->Set(0);
  for(int s = startSampleNum-const_preRange ; s < startSampleNum + const_postRange ; s++){
    gChTest->SetPoint(gChTest->GetN() , s , wf.at(s) );
    double simVal = -1;
    fitResponse.sig->getSignalValue(s, fitBase,fitStart, fitShape, fitAmp, simVal );
    gFitTest->SetPoint(gFitTest->GetN(),s,simVal);
  }

  if(1){
   //std::cout << fitResponse.status << std::endl;
   cTest->Clear();
   gChTest->SetMarkerStyle(21);
   gChTest->SetMarkerColor(kRed);
   gChTest->Draw("AP");
   gFitTest->Draw("LP");
   cTest->Update();
   usleep(10000);
   //char ct;
   //std::cin >> ct;
  }
  */
}
