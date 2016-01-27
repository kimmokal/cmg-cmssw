import FWCore.ParameterSet.Config as cms

# Define the CMSSW process
process = cms.Process("RERUN")

# Load the standard set of configuration modules
process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.StandardSequences.GeometryDB_cff')
process.load('Configuration.StandardSequences.MagneticField_38T_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

# Message Logger settings
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.destinations = ['cout', 'cerr']
process.MessageLogger.cerr.FwkReport.reportEvery = 1

# Set the process options -- Display summary at the end, enable unscheduled execution
process.options = cms.untracked.PSet( 
    allowUnscheduled = cms.untracked.bool(True),
    wantSummary = cms.untracked.bool(False) 
)

# How many events to process
process.maxEvents = cms.untracked.PSet( 
   input = cms.untracked.int32(10)
)

#configurable options =======================================================================
runOnData=False #data/MC switch
usePrivateSQlite=False #use external JECs (sqlite file)
useHFCandidates=True #create an additionnal NoHF slimmed MET collection if the option is set to false
applyResiduals=True #application of residual corrections. Have to be set to True once the 13 TeV residual corrections are available. False to be kept meanwhile. Can be kept to False later for private tests or for analysis checks and developments (not the official recommendation!).
#===================================================================


### External JECs =====================================================================================================

#from Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff import *
#process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
#from Configuration.AlCa.GlobalTag_condDBv2 import GlobalTag
from Configuration.AlCa.autoCond import autoCond
#GlobalTag = gtCustomise(GlobalTag, 'auto:run2_data', '')
if runOnData:
  process.GlobalTag.globaltag = autoCond['run2_data']
  #process.GlobalTag.globaltag = '75X_dataRun1_v2' #'74X_dataRun2_Prompt_v1'
else:
  process.GlobalTag.globaltag = 'MCRUN2_75_V5'
 # process.GlobalTag.globaltag = autoCond['run2_mc']
 # process.GlobalTag = GlobaTag(GlobalTag, 'auto:run2_mc', '')

if usePrivateSQlite:
    from CondCore.DBCommon.CondDBSetup_cfi import *
    import os
    if runOnData:
      era="Summer15_25nsV5_DATA"
    else:
      era="Summer15_25nsV6_MC"
      
    process.jec = cms.ESSource("PoolDBESSource",CondDBSetup,
                               connect = cms.string( "frontier://FrontierPrep/CMS_COND_PHYSICSTOOLS"),
                               toGet =  cms.VPSet(
            cms.PSet(
                record = cms.string("JetCorrectionsRecord"),
                tag = cms.string("JetCorrectorParametersCollection_"+era+"_AK4PF"),
                label= cms.untracked.string("AK4PF")
                ),
            cms.PSet(
                record = cms.string("JetCorrectionsRecord"),
                tag = cms.string("JetCorrectorParametersCollection_"+era+"_AK4PFchs"),
                label= cms.untracked.string("AK4PFchs")
                ),
            )
                               )
    process.es_prefer_jec = cms.ESPrefer("PoolDBESSource",'jec')


### Jet resolution
from CondCore.DBCommon.CondDBSetup_cfi import *
ERA = 'Summer15_25nsV6'
process.PoolDBESSource = cms.ESSource("PoolDBESSource",
        CondDBSetup,
        toGet = cms.VPSet(
            # Resolution
            cms.PSet(
                record = cms.string('JetResolutionRcd'),
                tag    = cms.string('JER_MC_PtResolution_%s_AK4PFchs' % ERA),
                label  = cms.untracked.string('AK4PFchs')
                ),
 
            # Scale factors
            cms.PSet(
                record = cms.string('JetResolutionScaleFactorRcd'),
                tag    = cms.string('JER_DATAMCSF_%s_AK4PFchs' % ERA),
                label  = cms.untracked.string('AK4PFchs')
                ),
            ),
        connect = cms.string('sqlite:JER_%s.db' % ERA)
        )



### =====================================================================================================


# Define the input source
if runOnData:
  #75X file : root://eoscms//eos/cms/store/relval/CMSSW_7_5_0/SingleElectron/MINIAOD/75X_dataRun1_HLT_v1_RelVal_electron2012D-v1/00000/A4BD1262-8F2B-E511-8470-002618943964.root
  #74X file : root://eoscms.cern.ch//store/data/Run2015B/JetHT/MINIAOD/PromptReco-v1/000/251/252/00000/263D331F-AF27-E511-969B-02163E012627.root
  fname = 'root://eoscms.cern.ch//store/data/Run2015B/JetHT/MINIAOD/PromptReco-v1/000/251/252/00000/263D331F-AF27-E511-969B-02163E012627.root' 
else:
  #75X file : root://eoscms.cern.ch//store/relval/CMSSW_7_5_0/RelValTTbar_13/MINIAODSIM/75X_mcRun2_asymptotic_v1-v1/00000/92A928E7-842A-E511-87CC-0025905A60E0.root
  #74X file : root://eoscms.cern.ch//store/mc/RunIISpring15DR74/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/MINIAODSIM/Asympt50ns_MCRUN2_74_V9A-v2/60000/001C7571-0511-E511-9B8E-549F35AE4FAF.root
  fname = 'root://eoscms.cern.ch//store/relval/CMSSW_8_0_0_pre4/RelValTTbar_13/MINIAODSIM/76X_mcRun2_asymptotic_v13-v1/00000/52384AF8-D2A5-E511-8F89-0CC47A4D7604.root'
  
# Define the input source
process.source = cms.Source("PoolSource", 
    fileNames = cms.untracked.vstring([ fname ])
)



### ---------------------------------------------------------------------------
### Removing the HF from the MET computation
### ---------------------------------------------------------------------------
if not useHFCandidates:
    process.noHFCands = cms.EDFilter("CandPtrSelector",
                                     src=cms.InputTag("packedPFCandidates"),
                                     cut=cms.string("abs(pdgId)!=1 && abs(pdgId)!=2 && abs(eta)<3.0")
                                     )

#jets are rebuilt from those candidates by the tools, no need to do anything else
### =================================================================================

from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD, runMETCorrectionsAndUncertainties

#default configuration for miniAOD reprocessing, change the isData flag to run on data
#for a full met computation, remove the pfCandColl input
runMetCorAndUncFromMiniAOD(process,
                           isData=runOnData,
                           )

if not useHFCandidates:
    runMetCorAndUncFromMiniAOD(process,
                               isData=runOnData,
                               pfCandColl=cms.InputTag("noHFCands"),
                               reclusterJets=True, #needed for NoHF
                               recoMetFromPFCs=True, #needed for NoHF
                               postfix="NoHF"
                               )

### -------------------------------------------------------------------
### the lines below remove the L2L3 residual corrections when processing data
### -------------------------------------------------------------------
if not applyResiduals:
    process.patPFMetT1T2Corr.jetCorrLabelRes = cms.InputTag("L3Absolute")
    process.patPFMetT1T2SmearCorr.jetCorrLabelRes = cms.InputTag("L3Absolute")
    process.patPFMetT2Corr.jetCorrLabelRes = cms.InputTag("L3Absolute")
    process.patPFMetT2SmearCorr.jetCorrLabelRes = cms.InputTag("L3Absolute")
    process.shiftedPatJetEnDown.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")
    process.shiftedPatJetEnUp.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")

    if not useHFCandidates:
          process.patPFMetT1T2CorrNoHF.jetCorrLabelRes = cms.InputTag("L3Absolute")
          process.patPFMetT1T2SmearCorrNoHF.jetCorrLabelRes = cms.InputTag("L3Absolute")
          process.patPFMetT2CorrNoHF.jetCorrLabelRes = cms.InputTag("L3Absolute")
          process.patPFMetT2SmearCorrNoHF.jetCorrLabelRes = cms.InputTag("L3Absolute")
          process.shiftedPatJetEnDownNoHF.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")
          process.shiftedPatJetEnUpNoHF.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")
### ------------------------------------------------------------------


process.MINIAODSIMoutput = cms.OutputModule("PoolOutputModule",
    compressionLevel = cms.untracked.int32(4),
    compressionAlgorithm = cms.untracked.string('LZMA'),
    eventAutoFlushCompressedSize = cms.untracked.int32(15728640),
    outputCommands = cms.untracked.vstring( "keep *_slimmedMETs_*_RERUN",
                                            "keep *_slimmedMETsNoHF_*_*",
                                            "keep *_patPFMet_*_*",
                                            "keep *_patPFMetT1_*_*",
                                            "keep *_patPFMetT1JetResDown_*_*",
                                            "keep *_patPFMetT1JetResUp_*_*",
                                            "keep *_patPFMetT1SmearTEST_*_*",
                                            "keep *_patPFMetT1SmearJetResDownTEST_*_*",
                                            "keep *_patPFMetT1SmearJetResUpTEST_*_*",
                                            "keep *_puppiForMET_*_*",
                                            "keep *_puppi_*_*",
                                            "keep *_patPFMetT1Puppi_*_*",
                                            "keep *_slimmedMETsPuppi_*_*",
                                            ),
    fileName = cms.untracked.string('corMETMiniAOD.root'),
    dataset = cms.untracked.PSet(
        filterName = cms.untracked.string(''),
        dataTier = cms.untracked.string('')
    ),
    dropMetaData = cms.untracked.string('ALL'),
    fastCloning = cms.untracked.bool(False),
    overrideInputFileSplitLevels = cms.untracked.bool(True)
)


process.MINIAODSIMoutput_step = cms.EndPath(process.MINIAODSIMoutput)


## ========================================
## test area
## ========================================



 #MET T1+Txy
#runMETCorrectionsAndUncertainties(process, metType="PF",
#                                  correctionLevel=["T1","Smear"],
#                                  computeUncertainties=True,
#                                  produceIntermediateCorrections=True,
#                                  addToPatDefaultSequence=False,
#                                  #jetCollection="selectedPatJets",
#                                  jetCollectionUnskimmed="slimmedJets",
#                                  electronCollection="slimmedElectrons",
#                                  muonCollection="slimmedMuons",
#                                  tauCollection="slimmedTaus",
#                                  photonCollection="slimmedPhotons",
#                                  pfCandCollection="packedPFCandidate",
#                                  runOnData=runOnData,
#                                  onMiniAOD=True,
#                                  reclusterJets=False,
#                                  recoMetFromPFCs=False,
#                                  autoJetCleaning="LepClean",
#                                  manualJetConfig=False,
#                                  jetFlavor="AK4PFchs",
#                                  jetCorLabelUpToL3=cms.InputTag('ak4PFCHSL1FastL2L3Corrector'),
#                                  jetCorLabelL3Res=cms.InputTag('ak4PFCHSL1FastL2L3ResidualCorrector'),
#                                  jecUncertaintyFile="",
#                                  postfix="TEST",
#                                  )


#process.load("CommonTools.PileupAlgos.Puppi_cff")
#process.puppi.candName       = cms.InputTag('packedPFCandidates')
#process.puppi.vertexName     = cms.InputTag('offlineSlimmedPrimaryVertices')
#process.puppi.useExistingWeights = cms.bool(True)
#process.puppi.useWeightsNoLep    = cms.bool(True)
#process.pfCandNoLep = cms.EDFilter("CandPtrSelector", src = cms.InputTag("packedPFCandidates"), cut =  cms.string("abs(pdgId) != 13 && abs(pdgId) != 11 && abs(pdgId) != 15"))
#process.pfCandLep   = cms.EDFilter("CandPtrSelector", src = cms.InputTag("packedPFCandidates"), cut = cms.string("abs(pdgId) == 13 || abs(pdgId) == 11 || abs(pdgId) == 15"))
#process.puppinolep = process.puppi.clone()
#process.puppinolep.candName = 'pfCandNoLep'
#process.puppiForMET = cms.EDProducer("CandViewMerger",src = cms.VInputTag( 'puppinolep','pfCandLep'))


#runMetCorAndUncFromMiniAOD(process,
#                           isData=runOnData,
#                           pfCandColl=cms.InputTag("puppiForMET"),
#                           reclusterJets=True, #needed for NoHF
#                           recoMetFromPFCs=True, #needed for NoHF
#                           postfix="Puppi"
#                           )
