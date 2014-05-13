#include <iostream>
#include "global.h"
#include "Dataset.h"
#include "Node.h"
#include "Miner.h"

Miner::Miner(){
}

Miner::~Miner(){
}

void Miner::run(Dataset* dataset, int maximumLevel,  int minimumSupport, double minimumConfidence, double minimumConfidenceInter, double smoothing, double reductionFactor, bool statistics, bool minimals, bool segmentals, bool singleTarget, bool limitedTarget, bool onlyTarget){
	// Retrieve data
	Node::m_nbItems = dataset->getNbItems();
	Node::m_minimumFrequency = minimumSupport;
	Node::m_minimumConfidence = minimumConfidence;
	Node::m_minimumConfidenceInter = minimumConfidenceInter;
	Node::m_smoothing = smoothing;
	Node::m_reductionFactor = reductionFactor;
	Node::m_statistics = statistics;
	Node::m_minimals = minimals;
	Node::m_segmentals = segmentals;
	Node::m_singleTarget = singleTarget;
	Node::m_limitedTarget = limitedTarget;
	Node::m_onlyTarget = onlyTarget;
	Node::m_transactions = dataset->getTransactions();
	Node::m_translation = dataset->getTranslation();
	Node::m_hierarchy = dataset->getHierarchy();
	Node::m_rootTarget = dataset->getRootTarget();
	// Initialize trie
	Node* rootNode = NULL;
	int maximumItemType = dataset->getMaximumItemType();
	ItemTypeList** m_hierarchy = Node::m_hierarchy;
	Node::m_itemTypeIsTarget = new bool[maximumItemType + 1];
	for(ITEMTYPE i = maximumItemType; i > 0; i--){
		ItemTypeList* itemHierarchy = m_hierarchy[i];
		while(itemHierarchy->m_next)
			itemHierarchy = itemHierarchy->m_next;
		rootNode = new Node(i, itemHierarchy->m_isTarget, itemHierarchy->m_isTarget, rootNode);
		Node::m_itemTypeIsTarget[i] = itemHierarchy->m_isTarget;
	}
	Node::m_root = rootNode;
	// Level-wise miner
	int level = 1, nbFrequent = 1;
	std::cerr << "Mining patterns (frequency: " << minimumSupport << ", confidence: " << minimumConfidence << ", confidence inter: " << minimumConfidenceInter << "):" << std::endl;
	std::cerr << "Modes:" << (minimals ? " min" : " max") << (segmentals ? " segs": "") << (singleTarget ? " st": "") << std::endl;
	while(nbFrequent && (maximumLevel == 0 || level <= maximumLevel) && level < MAX_LEVEL){
		std::cerr << "  ... level " << level << " ";
		if(level > 1){
			std::cerr << "generate ... ";
			std::cerr << "(" << rootNode->generate(level) << " candidates) ";
		}
		std::cerr << "count... ";
		rootNode->count(level);
		std::cerr << "filter... ";
		std::cerr << "(" << (nbFrequent = rootNode->filter(level)) << " frequent) ";
		std::cerr << "group... ";
		std::cerr << "(" << rootNode->group(level) << " minimals) ";
		std::cerr << std::endl;
		level++;
	}
	// Output patterns and statistics
	std::cerr << "Finished mining, outputing patterns ..." << std::endl;
	rootNode->output(level);
	if(statistics){
		std::cerr << "Statistics for frequent patterns and rules (max/min is maximal by default, or minimal if option has been set) :" << std::endl;
		std::cerr << "- patterns: " << Node::m_nbPatterns << " total, " << Node::m_nbMinimalOrMaximalPatterns << " max/min." << std::endl;
		std::cerr << "- rules: " << Node::m_nbRules << " total, " << Node::m_nbConfidentRules << " confident." << std::endl;
		std::cerr << "- max/min rules: " << Node::m_nbMinimalOrMaximalRules << " total, " << Node::m_nbConfidentMinimalOrMaximalRules << " confident." << std::endl;
		std::cerr << "- max/min info. rules: " << Node::m_nbInformativeRules << " total, " << Node::m_nbConfidentInformativeRules << " confident." << std::endl;
	}
	std::cerr << "Selected rules: " << Node::m_nbSelected << "." << std::endl;
}

