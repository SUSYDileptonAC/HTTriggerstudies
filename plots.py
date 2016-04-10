#!/usr/bin/env python

import sys
sys.path.append('cfg/')
from frameworkStructure import pathes
sys.path.append(pathes.basePath)

import os
import pickle

from messageLogger import messageLogger as log

import math

from array import array

import argparse	


import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
from ROOT import TCanvas, TEfficiency, TPad, TH1F, TH1I, THStack, TLegend, TMath, TGraphAsymmErrors, TF1, gStyle
ROOT.gROOT.SetBatch(True)

from defs import getRegion, getPlot, getRunRange, Backgrounds

from setTDRStyle import setTDRStyle
from helpers import readTrees, getDataHist, TheStack, totalNumberOfGeneratedEvents, Process

from corrections import triggerEffs, rSFOF
from centralConfig import regionsToUse, runRanges, backgroundLists, plotLists, systematics
from locations import locations

def getHistograms(path,plot,runRange,isMC,backgrounds,EM=False):


	treesEE = readTrees(path,"EE")
	treesEM = readTrees(path,"EMu")
	treesMM = readTrees(path,"MuMu")
		
	
	
	if isMC:
		
		eventCounts = totalNumberOfGeneratedEvents(path)	
		processes = []
		for background in backgrounds:
			processes.append(Process(getattr(Backgrounds,background),eventCounts))
		
		histoEE = TheStack(processes,runRange.lumi,plot,treesEE,"None",1.0,1.0,1.0).theHistogram		
		histoMM = TheStack(processes,runRange.lumi,plot,treesMM,"None",1.0,1.0,1.0).theHistogram

		
		if EM:
			histoEM = TheStack(processes,runRange.lumi,plot,treesEM,"None",1.0,1.0,1.0).theHistogram		
		
	else:
		histoEE = getDataHist(plot,treesEE)
		histoMM = getDataHist(plot,treesMM)
		if EM:
			histoEM = getDataHist(plot,treesEM)
	
	if EM:
		return histoEE , histoMM, histoEM
	else:
		return histoEE , histoMM

	
def plot(path,selection,plots,runRange,isMC,backgrounds,cmsExtra):
	

	
	for name in plots:
		plot = getPlot(name)
		plot.addRegion(selection)
		plot.cleanCuts()	
		plot.cuts = plot.cuts % runRange.runCut	


		if isMC:
			histEE, histMM = getHistograms(path,plot,runRange,True, backgrounds)	
		else:
			histEE, histMM = getHistograms(path,plot,runRange,False, backgrounds)	
			
		
		hCanvas = TCanvas("hCanvas", "Distribution", 800,800)
		
		plotPad = ROOT.TPad("plotPad","plotPad",0,0,1,1)
		setTDRStyle()
		plotPad.UseCurrentStyle()
		
		plotPad.Draw()	
		plotPad.cd()	
				
			
		latex = ROOT.TLatex()
		latex.SetTextFont(42)
		latex.SetTextAlign(31)
		latex.SetTextSize(0.04)
		latex.SetNDC(True)
		latexCMS = ROOT.TLatex()
		latexCMS.SetTextFont(61)
		latexCMS.SetTextSize(0.06)
		latexCMS.SetNDC(True)
		latexCMSExtra = ROOT.TLatex()
		latexCMSExtra.SetTextFont(52)
		latexCMSExtra.SetTextSize(0.045)
		latexCMSExtra.SetNDC(True)		

		intlumi = ROOT.TLatex()
		intlumi.SetTextAlign(12)
		intlumi.SetTextSize(0.03)
		intlumi.SetNDC(True)					
		

		logScale = plot.log

		if logScale == True:
			plotPad.SetLogy()
			
	
		yMax = histMM.GetBinContent(histMM.GetMaximumBin())
		if plot.yMax == 0:
			if logScale:
				yMax = yMax*1000
			else:
				yMax = yMax*1.5
							
		else: yMax = plot.yMax


		plotPad.DrawFrame(plot.firstBin,plot.yMin,plot.lastBin,yMax,"; %s ; %s" %(plot.xaxis,plot.yaxis))
		
		legend = ROOT.TLegend(0.65,0.7,0.9,0.9)
		legend.SetFillStyle(0)
		legend.SetBorderSize(0)	
		legend.AddEntry(histMM,"#mu#mu events","p")
		legend.AddEntry(histEE,"ee events","p")
		histMM.SetMarkerColor(ROOT.kRed)
		histMM.SetLineColor(ROOT.kRed)
		histMM.SetMarkerStyle(20)
		histEE.SetMarkerStyle(21)
		histMM.Draw("samepe")
		histEE.Draw("samepe")
		legend.Draw("same")
		ROOT.gPad.SetLogy(1)
		
		latex.DrawLatex(0.95, 0.96, "%s fb^{-1} (13 TeV)"%runRange.printval)
		

		latexCMS.DrawLatex(0.19,0.88,"CMS")
		if "Simulation" in cmsExtra:
			yLabelPos = 0.81	
		else:
			yLabelPos = 0.84	

		latexCMSExtra.DrawLatex(0.19,yLabelPos,"%s"%(cmsExtra))
		
		
		
		hCanvas.Print("fig/testPlots_%s_%s_%s_%s.pdf"%(selection.name,runRange.label,plot.variablePlotName,plot.additionalName))	
	
	
			
	
def main():



	parser = argparse.ArgumentParser(description='rMuE measurements.')
	
	parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=False,
						  help="Verbose mode.")
	parser.add_argument("-m", "--mc", action="store_true", dest="mc", default=False,
						  help="use MC, default is to use data.")
	parser.add_argument("-s", "--selection", dest = "selection" , action="append", default=[],
						  help="selection which to apply.")
	parser.add_argument("-p", "--plot", dest="plots", action="append", default=[],
						  help="select dependencies to study, default is all.")
	parser.add_argument("-r", "--runRange", dest="runRange", action="append", default=[],
						  help="name of run range.")
	parser.add_argument("-b", "--backgrounds", dest="backgrounds", action="append", default=[],
						  help="backgrounds to plot.")
	parser.add_argument("-x", "--private", action="store_true", dest="private", default=False,
						  help="plot is private work.")	

					
	args = parser.parse_args()



	if len(args.backgrounds) == 0:
		args.backgrounds = backgroundLists.default
	if len(args.plots) == 0:
		args.plots = plotLists.default
	if len(args.selection) == 0:
		
			args.selection.append("Inclusive")	
	

			
	if len(args.runRange) == 0:
		args.runRange.append(runRanges.name)		

	path = locations.dataSetPath

	

	cmsExtra = ""
	if args.private:
		cmsExtra = "Private Work"
		if args.mc:
			cmsExtra = "#splitline{Private Work}{Simulation}"
	elif args.mc:
		cmsExtra = "Simulation"	
	else:
		cmsExtra = "Preliminary"
	for runRangeName in args.runRange:
		runRange = getRunRange(runRangeName)
	
		for selectionName in args.selection:
			
			selection = getRegion(selectionName)

			plot(path,selection,args.plots,runRange,args.mc,args.backgrounds,cmsExtra)		
		 	

main()
