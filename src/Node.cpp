#include <iostream>
#include <stdlib.h>
#include "global.h"
#include "Node.h"

int Node::m_minimumFrequency = 1;
double Node::m_minimumConfidence = -1;
double Node::m_minimumConfidenceInter = 0;
double Node::m_smoothing = 0;
double Node::m_reductionFactor = 0;
bool Node::m_statistics = false;
bool Node::m_minimals = false;
bool Node::m_segmentals = false;
bool Node::m_singleTarget = false;
bool Node::m_limitedTarget = false;
bool Node::m_onlyTarget = false;
bool Node::m_debug = false;
//bool Node::m_debug = true;
bool Node::m_siblings = true;
//bool Node::m_siblings = false;
bool Node::m_duplicates = true;
//bool Node::m_duplicates = false;
Node* Node::m_root = NULL;
int Node::m_nbItems = 0;
Transaction* Node::m_transactions = NULL;
char** Node::m_translation = NULL;
ItemTypeList** Node::m_hierarchy = NULL;
bool* Node::m_itemTypeIsTarget = NULL;
ITEMTYPE Node::m_rootTarget = 0;
int Node::m_nbPatterns = 0;
int Node::m_nbMinimalOrMaximalPatterns = 0;
int Node::m_nbRules = 0;
int Node::m_nbConfidentRules = 0;
int Node::m_nbMinimalOrMaximalRules = 0;
int Node::m_nbConfidentMinimalOrMaximalRules = 0;
int Node::m_nbInformativeRules = 0;
int Node::m_nbConfidentInformativeRules = 0;
int Node::m_nbSelected = 0;

Node::Node(ITEMTYPE item, bool isTarget, bool isTargetBegin, Node* alt){
	m_itemType = item;
	m_isTarget = isTarget;
	m_isTargetBegin = isTargetBegin;
	m_nbTarget = m_isTarget ? 1 : 0;
	m_frequency = 0;
	m_frequencyTargetSequence = 0;
	m_isMined = false;
	m_alt = alt;
	m_next = NULL;
	m_maximalSibling = NULL;
	m_minimalHierarchyLeft = NULL;
	m_maximalHierarchy = NULL;
	m_nextDuplicate = false;
	m_minimalLeft = NULL;
	m_maximalLeft = NULL;
	m_minimalRight = NULL;
	m_maximalRight = NULL;
	m_minimalManyfold = NULL;
	m_maximalManyfold = NULL;
	m_minimalTarget = NULL;
	m_maximalTarget = NULL;
	m_segmentLength = 0;
}

Node::~Node(){
	ItemTypeList* maximalSiblingToDelete = NULL;
	while(m_maximalSibling){
		maximalSiblingToDelete = m_maximalSibling;
		m_maximalSibling = m_maximalSibling->m_next;
		delete maximalSiblingToDelete;
	}
}

Node* Node::findNodeForItemType(ITEMTYPE itemType){
	if(m_itemType == itemType)
		return this;
	ItemTypeList* maximalSibling = m_maximalSibling;
	while(maximalSibling && maximalSibling->m_itemType < itemType)
		maximalSibling = maximalSibling->m_next;
	if(maximalSibling && maximalSibling->m_itemType == itemType)
		return this;
	if(m_alt && m_alt->m_itemType <= itemType)
		return m_alt->findNodeForItemType(itemType);
	return NULL;
}

Node* Node::findNodeForPattern(int length, ITEMTYPE* pattern, int currentLength){
	Node* nextNode = findNodeForItemType(pattern[currentLength]);
	if(currentLength == length - 1)
		return nextNode;
	if(nextNode && nextNode->m_next)
		return nextNode->m_next->findNodeForPattern(length, pattern, currentLength + 1);
	return NULL;
}

bool Node::hasSameSegmentsAs(Node* node){
	return node->m_frequency == m_frequency && node->m_segmentLength == m_segmentLength;
}

bool Node::hasSimilarFrequencyAs(Node* node, int fold){
	// Where node is more general (more frequent) than self
	return (double)(fold*node->m_frequency - m_frequency)/(double)(fold*node->m_frequency) <= m_reductionFactor;
}

bool Node::itemGeneralizesToItemType(Item* item, ITEMTYPE itemType){
	// Looks for current item
	if(itemTypeGeneralizesToItemType(item->m_itemType, itemType))
		return true;
	// Else looks in alt
	if(item->m_alt)
		return itemGeneralizesToItemType(item->m_alt, itemType);
	return false;
}

bool Node::itemTypeGeneralizesToItemType(ITEMTYPE specificItemType, ITEMTYPE generalItemType){
	// Looks if current hierarchy contains item type
	ItemTypeList* itemHierarchy = m_hierarchy[specificItemType];
	while(itemHierarchy){
		if(itemHierarchy->m_itemType == generalItemType)
			return true;
		itemHierarchy = itemHierarchy->m_next;
	}
	return false;
}

int Node::generate(int level){
	ITEMTYPE pattern[level + 1];
	return generate(level, 1, pattern);
}

int Node::generate(int level, int length, ITEMTYPE* pattern){
	int nbCandidates = 0;
	pattern[length - 1] = m_itemType;
	// See next nodes
	if(m_next && !m_nextDuplicate && !m_next->m_isMined)
		nbCandidates += m_next->generate(level, length + 1, pattern);
	// Generate for current level
	if(length == level - 1){
		// If minimal hierarchy, just copy hierarchy's next node
		if(m_duplicates && m_minimalHierarchyLeft && !m_isTarget && !m_isTargetBegin && hasSameSegmentsAs(m_minimalHierarchyLeft)){
			m_next = m_minimalHierarchyLeft->m_next;
			m_nextDuplicate = true;
			// Else looks for overlapping nodes
		}else{
			bool isOnlyTarget = m_nbTarget == length;
			bool isOnlyTargetUnfrequent = isOnlyTarget && m_frequency < m_minimumFrequency;
			Node* overlappingNode = m_root;
			if(length > 1)
				overlappingNode = overlappingNode->findNodeForPattern(length - 1, &pattern[1])->m_next;
			// Generates new next nodes
			while(overlappingNode){
				bool overlappingNodeIsTarget = overlappingNode->m_isTarget;
				bool overlappingNodeOnlyTarget = m_onlyTarget && overlappingNodeIsTarget;
				if((!isOnlyTargetUnfrequent || overlappingNodeOnlyTarget) && (!m_singleTarget || length == 1 || !m_nbTarget || isOnlyTarget == overlappingNodeIsTarget) && (!m_limitedTarget || length == 1 || !m_isTarget || isOnlyTarget && overlappingNodeIsTarget || overlappingNodeIsTarget)){
					nbCandidates++;
					insertNextNode(overlappingNode->m_itemType, overlappingNodeIsTarget);
					ItemTypeList* overlappingMaximalSibling = overlappingNode->m_maximalSibling;
					while(overlappingMaximalSibling){
						nbCandidates++;
						insertNextNode(overlappingMaximalSibling->m_itemType, overlappingMaximalSibling->m_isTarget);
						overlappingMaximalSibling = overlappingMaximalSibling->m_next;
					}
				}
				overlappingNode = overlappingNode->m_alt;
			}
		}
	}
	// See alternatives
	if(m_alt)
		nbCandidates += m_alt->generate(level, length, pattern);
	return nbCandidates;
}

void Node::insertNextNode(ITEMTYPE itemType, bool isTarget){
	Node* newNode = new Node(itemType, isTarget, m_isTargetBegin);
	if(!m_next || m_next->m_itemType > itemType){
		// If no next, create it
		newNode->m_alt = m_next;
		m_next = newNode;
	}else{
		// If next, insert node
		Node* nextNode = m_next;
		while(nextNode->m_alt && nextNode->m_alt->m_itemType < itemType)
			nextNode = nextNode->m_alt;
		newNode->m_alt = nextNode->m_alt;
		nextNode->m_alt = newNode;
	}
	newNode->m_nbTarget += m_nbTarget;
}

void Node::count(int level){
	// Counts patterns for all transactions and all items
	Transaction* currentTransaction = m_transactions;
	while(currentTransaction){
		Item* currentItem = currentTransaction->m_items;
		Item* previousItem = NULL;
		int currentTransactionNbItem = currentTransaction->m_nbItems;
		while(currentItem && currentTransactionNbItem >= level){
			countItem(level, 1, currentItem, !previousItem || !previousItem->m_isTarget, previousItem);
			while(currentItem && currentItem->m_isTarget){
				currentItem = currentItem->m_next;
				currentTransactionNbItem--;
			}
			previousItem = currentItem;
			if(currentItem){
				currentItem = currentItem->m_next;
				currentTransactionNbItem--;
			}
		}
		currentTransaction = currentTransaction->m_next;
	}
}

void Node::countItem(int level, int length, Item* item, bool isTargetSequence, Item* previousItem, ITEMTYPE previousItemType, bool latestItemIsTarget, int segmentLength, Item* skippedItems, int skippedLength){
	// Checks if item is skippable as target
	if(m_minimumConfidence >= 0 && item->m_next && item->m_isTarget)
		countItem(level, length, item->m_next, false, previousItem, previousItemType, latestItemIsTarget, segmentLength, skippedItems ? skippedItems : item, skippedLength + 1);
	// Checks if item is skippable as segmental
	if(m_segmentals && item->m_next && !item->m_isTarget && previousItemType && !latestItemIsTarget && itemGeneralizesToItemType(item, previousItemType))
		countItem(level, length, item->m_next, isTargetSequence, item, previousItemType, latestItemIsTarget, segmentLength + 1);
	// Count current item
	countItemAlt(level, length, item, item, isTargetSequence, previousItem, previousItemType, segmentLength, skippedItems, skippedLength);
}

void Node::countItemAlt(int level, int length, Item* item, Item* itemAlt, bool isTargetSequence, Item* previousItem, ITEMTYPE previousItemType, int segmentLength, Item* skippedItems, int skippedLength){
	// Also count other alt
	if(itemAlt->m_alt)
		countItemAlt(level, length, item, itemAlt->m_alt, isTargetSequence, previousItem, previousItemType, segmentLength, skippedItems, skippedLength);
	// We look for item type and its hierarchy parents among alt nodes
	Node* currentNode = this;
	ItemTypeList* hierarchyItem = m_hierarchy[itemAlt->m_itemType];
	while(hierarchyItem && currentNode && !currentNode->m_isMined){
		ITEMTYPE hierarchyItemType = hierarchyItem->m_itemType;
		bool hierarchyIsTarget = m_itemTypeIsTarget[hierarchyItemType];
		// Counts item in trie
		if(isCountable(level, length, item, itemAlt, hierarchyItemType, previousItem, previousItemType, skippedItems, skippedLength)){
			while(currentNode && !currentNode->m_isMined && currentNode->m_itemType < hierarchyItemType)
				currentNode = currentNode->m_alt;
			if(currentNode && !currentNode->m_isMined && currentNode->m_itemType == hierarchyItemType){
				// If pattern is complete count node's frequency
				if(length == level){
					currentNode->m_frequency++;
					if(isTargetSequence && hierarchyIsTarget && (!item->m_next || !item->m_next->m_isTarget))
						currentNode->m_frequencyTargetSequence++;
					// For segmentals, set last segment length for optimizations
					if(m_segmentals){
						int hierarchySegmentLength = segmentLength;
						if(!hierarchyIsTarget){
							Item* itemNext = item;
							while(itemNext){
								itemNext = itemNext->m_next;
								while(itemNext && itemNext->m_isTarget)
									itemNext = itemNext->m_next;
								if(itemNext && itemGeneralizesToItemType(itemNext, hierarchyItemType))
									hierarchySegmentLength++;
								else
									itemNext = NULL;
							}
						}
						currentNode->m_segmentLength += hierarchySegmentLength;
					}
					// Otherwise go ahead in database if node is not duplicate
				}else if(item->m_next && currentNode->m_next && !currentNode->m_nextDuplicate)
					currentNode->m_next->countItem(level, length + 1, item->m_next, isTargetSequence && hierarchyIsTarget, hierarchyIsTarget ? previousItem : item, hierarchyIsTarget ? previousItemType : hierarchyItemType, hierarchyIsTarget, segmentLength);
			}
		}
		hierarchyItem = hierarchyItem->m_next;
	}
}

bool Node::isCountable(int level, int length, Item* currentItem, Item* currentItemAlt, ITEMTYPE currentItemType, Item* previousItem, ITEMTYPE previousItemType, Item* skippedItems, int skippedLength){
	// Checks if item type is present later in alt
	if(currentItemAlt->m_alt && itemGeneralizesToItemType(currentItemAlt->m_alt, currentItemType))
		return false;
	// Checks if item type is in skipped items list
	if(skippedItems){
		while(skippedLength){
			if(itemGeneralizesToItemType(skippedItems, currentItemType))
				return false;
			skippedItems = skippedItems->m_next;
			skippedLength--;
		}
	}
	// Checks if item is a valid segmental
	if(m_segmentals){
		// Inside or ending pattern
		if(previousItemType){
			// Inside pattern
			if(!m_itemTypeIsTarget[currentItemType]){
				if(itemTypeGeneralizesToItemType(previousItemType, currentItemType))
					return false;
				if(itemTypeGeneralizesToItemType(currentItemType, previousItemType))
					return false;
				ItemTypeList* hierarchyCurrentItemType = m_hierarchy[currentItemType];
				while(itemTypeGeneralizesToItemType(previousItemType, hierarchyCurrentItemType->m_itemType))
					hierarchyCurrentItemType = hierarchyCurrentItemType->m_next;
				if(itemGeneralizesToItemType(previousItem, hierarchyCurrentItemType->m_itemType))
					return false;
				ItemTypeList* hierarchyPreviousItemType = m_hierarchy[previousItemType];
				while(itemTypeGeneralizesToItemType(currentItemType, hierarchyPreviousItemType->m_itemType))
					hierarchyPreviousItemType = hierarchyPreviousItemType->m_next;
				if(itemGeneralizesToItemType(currentItem, hierarchyPreviousItemType->m_itemType))
					return false;
			// Ending of pattern, checks patterns is not a bad segment for target
			}else if(length == level && currentItem->m_next && itemGeneralizesToItemType(currentItem->m_next, m_hierarchy[previousItemType]->m_itemType)){
				return false;
			}
			// Beginning of pattern, checks pattern has not began before (including a bad segment for target)
		}else if(previousItem && !m_itemTypeIsTarget[currentItemType] && itemGeneralizesToItemType(previousItem, length == 1 ? currentItemType : m_hierarchy[currentItemType]->m_itemType))
			return false;
	}
	return true;
}

int Node::filter(int level){
	ITEMTYPE pattern[level];
	if(m_debug)
		outputLevel(level, 1, pattern);
	int nbFrequent = filter(level, 1, pattern, this);
	prune(level, 1);
	return nbFrequent;
}

int Node::filter(int level, int length, ITEMTYPE* pattern, Node* siblingNodes){
	pattern[length - 1] = m_itemType;
	int nbFrequent = 0;
	// See next nodes
	if(m_next && !m_nextDuplicate && !m_next->m_isMined)
		nbFrequent += m_next->filter(level, length + 1, pattern, m_next);
	// Filter current level nodes
	if(length == level){
		// Checks if any alt node that we are hierarchy of has same frequency, than add it as maximal sibling (but for target types)
		if(m_frequency >= m_minimumFrequency){
			nbFrequent++;
			// Looks for maximal siblings
			if(m_siblings && !m_isTarget){
				Node* altNode = m_alt;
				ItemTypeList* currentMaximalSibling = NULL;
				while(altNode){
					// If same frequency groups nodes together using maximal sibling
					if(itemTypeGeneralizesToItemType(altNode->m_itemType, m_itemType) && hasSameSegmentsAs(altNode)){
						nbFrequent++;
						ItemTypeList* item = new ItemTypeList;
						item->m_itemType = altNode->m_itemType;
						item->m_isTarget = altNode->m_isTarget;
						if(!m_maximalSibling)
							m_maximalSibling = item;
						else
							currentMaximalSibling->m_next = item;
						currentMaximalSibling = item;
						altNode->m_frequency = 0;
					}
					altNode = altNode->m_alt;
				}
				if(currentMaximalSibling)
					currentMaximalSibling->m_next = NULL;
			}
			// If not frequent, mark it to be deleted
		}else if(!m_onlyTarget || m_nbTarget != length)
			m_frequency = 0;
	}
	// See alt nodes
	if(m_alt)
		nbFrequent += m_alt->filter(level, length, pattern, siblingNodes);
	return nbFrequent;
}

void Node::prune(int level, int length, bool previousIsDuplicate){
	// See alt nodes
	if(m_alt)
		m_alt->prune(level, length, previousIsDuplicate);
	// See next nodes
	if(m_next && !m_next->m_isMined)
		m_next->prune(level, length + 1, previousIsDuplicate || m_nextDuplicate);
	// Prune next nodes that have null frequency
	if(length == level - 1 && m_next && !m_next->m_frequency){
		Node* nodeToDelete = m_next;
		m_next = m_next->m_alt;
		if(!previousIsDuplicate && !m_nextDuplicate)
			delete nodeToDelete;
	}
	// Prune alt nodes that have null frequency
	if(length == level && m_alt && !m_alt->m_frequency){
		Node* nodeToDelete = m_alt;
		m_alt = m_alt->m_alt;
		delete nodeToDelete;
	}
	// Determines if node is pruned for counting
	if(length < level)
		m_isMined = (!m_next || m_next->m_isMined) && (!m_alt || m_alt->m_isMined);
}

int Node::group(int level){
	ITEMTYPE pattern[level];
	return group(level, 1, pattern, true, !m_minimals);
}

int Node::group(int level, int length, ITEMTYPE* pattern, bool leftIsMinimalHierarchy, bool leftIsMaximalHierarchy){
	int nbMinimals = 0;
	// See alt nodes
	if(m_alt)
		nbMinimals += m_alt->group(level, length, pattern, leftIsMinimalHierarchy, leftIsMaximalHierarchy);
	// Prepares for current node
	pattern[length - 1] = m_itemType;
	ItemTypeList* maximalSibling = m_maximalSibling;
	if(maximalSibling) while(maximalSibling->m_next)
		maximalSibling = maximalSibling->m_next;
	// Set maximals and minimals for current node
	if(length == level && length > m_nbTarget){
		// Finds hierarchy minimals and maximals
		if(m_debug){
			std::cout << "Grouping: ";
			outputNodePattern(length, pattern);
			std::cout << "- hierarchy" << std::endl;
		}
		m_root->groupHierarchy(level, 1, pattern, this, leftIsMinimalHierarchy, leftIsMaximalHierarchy && !maximalSibling);
		if(!m_minimals && leftIsMaximalHierarchy && maximalSibling){
			pattern[length - 1] = maximalSibling->m_itemType;
			m_root->groupHierarchy(level, 1, pattern, this, false);
		}
		// Only find left, right and target minimals/maximals for selected nodes
		bool isMinimalOrMaximal = (m_minimals && leftIsMinimalHierarchy && !m_minimalHierarchyLeft || !m_minimals && leftIsMaximalHierarchy && !m_maximalHierarchy);
		if(length > 1 && isMinimalOrMaximal){
			pattern[length - 1] = !m_minimals && maximalSibling ? maximalSibling->m_itemType : m_itemType;
			// Finds left and right minimals/maximals if not target types
			if(m_debug)
				std::cout << "- left/right" << std::endl;
			if(!m_itemTypeIsTarget[pattern[0]]){
				Node* minimalLeft = m_root->findNodeForPattern(length - 1, &pattern[1]);
				if(hasSimilarFrequencyAs(minimalLeft)){
					m_minimalLeft = minimalLeft;
					minimalLeft->m_maximalLeft = this;
				}
			}
			if(!m_itemTypeIsTarget[pattern[length - 1]]){
				Node* minimalRight = m_root->findNodeForPattern(length - 1, pattern);
				if(hasSimilarFrequencyAs(minimalRight)){
					m_minimalRight = minimalRight;
					minimalRight->m_maximalRight = this;
				}
			}
			// Finds manyfold minimals/maximals (pattern is manyfold a subpattern and has double frequency)
			if(m_debug)
				std::cout << "- Manyfolds" << std::endl;
			for(int i = 1; !m_minimalManyfold && i <= length/2; i++){
				if(!length%i){
					bool isManyfold = true;
					int lengthFold= length/i;
					for(int j = 0; isManyfold && j < lengthFold; j++)
						for(int k = 0; isManyfold && k < i; k++)
							isManyfold &= pattern[i] == pattern[j + k*lengthFold];
					if(isManyfold){
						Node* minimalManyfold = m_root->findNodeForPattern(lengthFold, pattern);
						if(hasSimilarFrequencyAs(minimalManyfold, i)){
							m_minimalManyfold = minimalManyfold;
							minimalManyfold->m_maximalManyfold = this;
						}
					}
				}
			}
			// Finds target minimals/maximals
			if(m_debug)
				std::cout << "- target" << std::endl;
			Node* minimalTarget = NULL;
			for(int i = 0; i < length; i++){
				Node* minimalTargetNext = minimalTarget ? minimalTarget->m_next : m_root;
				Node* nextNode = minimalTargetNext->findNodeForItemType(pattern[i]);
				if(nextNode->m_isTarget && pattern[i] != m_rootTarget){
					Node* minimalTargetWithoutTarget = i == length - 1 ? minimalTarget : minimalTargetNext->findNodeForPattern(length - i - 1, &pattern[i + 1]);
					if(hasSimilarFrequencyAs(minimalTargetWithoutTarget)){
						if(!m_minimalTarget)
							m_minimalTarget = minimalTargetWithoutTarget;
						if(!minimalTargetWithoutTarget->m_maximalTarget)
							minimalTargetWithoutTarget->m_maximalTarget = this;
					}
				}
				minimalTarget = nextNode;
			}
		}
		// Counts number of minimals
		if(m_debug)
			std::cout << "Grouped" << std::endl;
		if(!m_minimalHierarchyLeft && !m_minimalLeft && !m_minimalRight)
			nbMinimals++;
		// See next nodes
	}else if(m_next && !m_next->m_isMined){
		bool nextIsMinimalHierarchy = leftIsMinimalHierarchy && !m_minimalHierarchyLeft;
		bool maximalSiblingNextIsMaximalHierarchy = leftIsMaximalHierarchy && !m_maximalHierarchy;
		bool nextIsMaximalHierarchy = maximalSibling ? false : maximalSiblingNextIsMaximalHierarchy;
		if(nextIsMinimalHierarchy || nextIsMaximalHierarchy)
			nbMinimals += m_next->group(level, length + 1, pattern, nextIsMinimalHierarchy, nextIsMaximalHierarchy);
		if(!m_minimals && !nextIsMaximalHierarchy && maximalSiblingNextIsMaximalHierarchy){
			pattern[length - 1] = maximalSibling->m_itemType;
			nbMinimals += m_next->group(level, length + 1, pattern, false);
		}
	}
	return nbMinimals;
}

void Node::groupHierarchy(int level, int length, ITEMTYPE* pattern, Node* maximalNode, bool isMinimalHierarchy, bool isMaximalHierarchy, ITEMTYPE previousItemType, bool latestItemTypeIsTarget){
	// Retrieve hierarchy for current item
	ItemTypeList* hierarchyItem = m_hierarchy[pattern[length - 1]];
	// If target or border target, do not examine hierarchy
	bool targetNoHierarchy = false;
	if(hierarchyItem->m_isTarget)
		targetNoHierarchy = true;
	if(!targetNoHierarchy && length > 1){
		targetNoHierarchy = true;
		for(int i = 0; targetNoHierarchy && i < length - 1; i++)
			targetNoHierarchy &= m_itemTypeIsTarget[pattern[i]];
	}
	if(!targetNoHierarchy && length < level){
		targetNoHierarchy = true;
		for(int i = length; targetNoHierarchy && i < level; i++)
			targetNoHierarchy &= m_itemTypeIsTarget[pattern[i]];
	}
	if (targetNoHierarchy) while(hierarchyItem->m_next)
		hierarchyItem = hierarchyItem->m_next;
	// Looks for generalizations
	while(hierarchyItem){
		ITEMTYPE hierarchyItemType = hierarchyItem->m_itemType;
		bool hierarchyIsTarget = hierarchyItem->m_isTarget;
		if(m_debug){
			std::cout << "   " << length << ": ";
			outputItemType(hierarchyItemType);
			std::cout << std::endl;
		}
		// Searches current pattern item type hierarchy node (taking into account segmentals)
		Node* hierarchyNode = NULL;
		if(m_segmentals && previousItemType && previousItemType == hierarchyItemType)
			hierarchyNode = latestItemTypeIsTarget ? NULL : this;
		else if(m_segmentals && (itemTypeGeneralizesToItemType(previousItemType, hierarchyItemType) || itemTypeGeneralizesToItemType(hierarchyItemType, previousItemType)))
			hierarchyNode = NULL;
		else
			hierarchyNode = (length == 1 ? this : m_next)->findNodeForItemType(hierarchyItemType);
		// Examines hierarchy node
		if(hierarchyNode && !hierarchyNode->m_nextDuplicate){
			// Looks for frequency of complete pattern if possible
			Node* hierarchyPatternNode = NULL;
			bool hierarchyIsSegmentalValid = true;
			if(length == level)
				hierarchyPatternNode = hierarchyNode;
			else{

				if(m_segmentals && m_itemTypeIsTarget[pattern[length]]){
					ITEMTYPE nextItemType = 0;
					for(int i = length; !nextItemType && i < level; i++)
						if(!m_itemTypeIsTarget[pattern[i]])
							nextItemType = pattern[i];
					if(!itemTypeGeneralizesToItemType(nextItemType, hierarchyItemType))
						hierarchyPatternNode = hierarchyNode->m_next->findNodeForPattern(level - length, &pattern[length]);
				}else{
					int nextLength = length;
					if(m_segmentals){
						while(nextLength < level && itemTypeGeneralizesToItemType(pattern[nextLength], hierarchyItemType))
							nextLength++;
						while(nextLength < level && m_itemTypeIsTarget[pattern[nextLength]])
							nextLength++;
						if(nextLength < level)
							hierarchyIsSegmentalValid = !itemTypeGeneralizesToItemType(hierarchyItemType, pattern[nextLength]) && !itemTypeGeneralizesToItemType(pattern[nextLength], hierarchyItemType);
					}
					if(hierarchyIsSegmentalValid)
						hierarchyPatternNode = nextLength == level ? hierarchyNode : hierarchyNode->m_next->findNodeForPattern(level - nextLength, &pattern[nextLength]);
				}
			}
			// If found, sets maximal and minimal nodes
			if(hierarchyPatternNode && maximalNode->hasSimilarFrequencyAs(hierarchyPatternNode)){
				// Triggers recursively grouping on next node
				if(length < level)
					hierarchyNode->groupHierarchy(level, length + 1, pattern, maximalNode, isMinimalHierarchy, isMaximalHierarchy, hierarchyIsTarget ? previousItemType : hierarchyItemType, hierarchyIsTarget);
				// If found set minimals and maximals
				else if(hierarchyPatternNode != maximalNode){
					if(m_debug)
						std::cout << "   > set maximal" << std::endl;
					if(isMinimalHierarchy && !maximalNode->m_minimalHierarchyLeft)
						maximalNode->m_minimalHierarchyLeft = hierarchyPatternNode;
					if(isMaximalHierarchy && !hierarchyPatternNode->m_maximalHierarchy)
						hierarchyPatternNode->m_maximalHierarchy = maximalNode;
				}
			}
		}
		// See next hierarchy item
		hierarchyItem = hierarchyItem->m_next;
	}
}

void Node::output(int level){
	ITEMTYPE pattern[level];
	//outputLevel(level, 1, pattern, true);
	output(1, pattern);
}

void Node::output(int length, ITEMTYPE* pattern, bool leftIsMinimalHierarchy, bool leftIsMaximalHierarchy){
	// If target alone, output its frequency
	if(this == m_root)
		std::cout << "ANY (freq:" << m_nbItems << ")" << std::endl;
	if(length == 1 && m_itemType == m_rootTarget)
		std::cout << "NE (freq:" << m_frequency << ")" << std::endl;
	if(m_nbTarget == length && (length == 1 || m_onlyTarget) && m_itemType != m_rootTarget){
		pattern[length - 1] = m_itemType;
		for(int i = 0; i < length; i++){
			if(m_translation)
				std::cout << m_translation[pattern[i]];
			else
				std::cout << pattern[i];
			std::cout << " ";
		}
		std::cout << "(freq:" << m_frequency << ",freqts:" << m_frequencyTargetSequence << ")" << std::endl;
	}
	// Do output for current item type and for each sibling
	bool isMainSibling = true;
	ItemTypeList* maximalSibling = m_maximalSibling;
	if(!m_statistics && maximalSibling){
		if(m_minimals)
			maximalSibling = NULL;
		else if(maximalSibling){
			isMainSibling = false;
			while(maximalSibling->m_next)
				maximalSibling = maximalSibling->m_next;
		}
	}
	while(isMainSibling || maximalSibling){
		// Sets current sibling item type
		pattern[length - 1] = isMainSibling ? m_itemType : maximalSibling->m_itemType;
		if(pattern[length - 1] != m_rootTarget){
			// Checks pattern properties
			m_nbPatterns++;
			bool isMinimalSibling = isMainSibling;
			bool isMaximalSibling = !maximalSibling || !isMainSibling && !maximalSibling->m_next;
			bool isMinimalHierarchy = leftIsMinimalHierarchy && isMinimalSibling && !m_minimalHierarchyLeft;
			bool isMaximalHierarchy = leftIsMaximalHierarchy && isMaximalSibling && !m_maximalHierarchy;
			// See next nodes
			if(m_next)
				m_next->output(length + 1, pattern, isMinimalHierarchy, isMaximalHierarchy);
			// Count and output current level nodes depending on conditions (minimals, maximals, number of targets, etc.)
			bool isMinimal = isMinimalHierarchy && !m_minimalLeft && !m_minimalRight && !m_minimalManyfold;
			bool isMaximal = isMaximalHierarchy && !m_maximalLeft && !m_maximalRight && !m_maximalManyfold;
			bool isMinimalOrMaximal = m_minimals && isMinimal || !m_minimals && isMaximal;
			if(isMinimalOrMaximal)
				m_nbMinimalOrMaximalPatterns++;
			bool isRule = m_nbTarget && length - m_nbTarget;
			if(isRule){
				m_nbRules++;
				Node* nodeWithoutTarget = NULL, *nodeWithRootTarget = NULL;
				int frequencyWithOneTarget[length];
				int frequencyWithOneRootTarget[length];
				ITEMTYPE previousItemTypeWithoutTarget = 0;
				for(int i = 0; i < length; i++){
					Node* nodeWithoutTargetNext = nodeWithoutTarget ? nodeWithoutTarget->m_next : m_root;
					Node* nextNode = nodeWithoutTargetNext->findNodeForItemType(pattern[i]);
					if(nextNode->m_isTarget){
						Node* nodeWithOneTarget = nextNode;
						Node* nodeWithOneRootTarget = nodeWithoutTargetNext->findNodeForItemType(m_rootTarget);
						ITEMTYPE previousItemTypeWithOneTarget = 0, previousItemTypeWithRootTarget = 0;
						for(int j = i + 1; j < length; j++){
							Node* nextNodeWithOneTarget = nodeWithOneTarget->m_next->findNodeForItemType(pattern[j]);
							if(!nextNodeWithOneTarget->m_isTarget){
								nodeWithOneTarget = nextNodeWithOneTarget;
								previousItemTypeWithOneTarget = pattern[j];
							}
							Node* nextNodeWithOneRootTarget = nodeWithOneRootTarget->m_next->findNodeForItemType(pattern[j]);
							if(!nextNodeWithOneRootTarget->m_isTarget){
								nodeWithOneRootTarget = nextNodeWithOneRootTarget;
								previousItemTypeWithRootTarget = pattern[j];
							}
						}
						frequencyWithOneTarget[i] = nodeWithOneTarget->m_frequency;
						frequencyWithOneRootTarget[i] = nodeWithOneRootTarget->m_frequency;
					}else{
						previousItemTypeWithoutTarget = pattern[i];
						frequencyWithOneTarget[i] = 0;
						frequencyWithOneRootTarget[i] = 0;
						nodeWithoutTarget = nextNode;
					}
					if(!nodeWithRootTarget || !nodeWithRootTarget->m_isTarget || !nextNode->m_isTarget)
						nodeWithRootTarget = (nodeWithRootTarget ? nodeWithRootTarget->m_next : m_root)->findNodeForItemType(nextNode->m_isTarget ? m_rootTarget : pattern[i]);
				}
				double confidence = (double)m_frequency/nodeWithoutTarget->m_frequency;
				bool isConfidentRule = confidence >= m_minimumConfidence;
				bool isConfidentInterRule = (double)m_frequency/nodeWithRootTarget->m_frequency >= m_minimumConfidenceInter;
				bool isMaximalTarget = !m_maximalTarget;
				if(isConfidentRule && isConfidentInterRule)
					m_nbConfidentRules++;
				if(isMinimalOrMaximal){
					m_nbMinimalOrMaximalRules++;
					if(isConfidentRule)
						m_nbConfidentMinimalOrMaximalRules++;
					if(isMaximalTarget){
						m_nbInformativeRules++;
						if(isConfidentRule)
							m_nbConfidentInformativeRules++;
					}
				}
				if(isMinimalOrMaximal && isConfidentRule && isMaximalTarget && isConfidentInterRule){
					m_nbSelected++;
					for(int i = 0; i < length; i++){
						if(m_translation)
							std::cout << m_translation[pattern[i]];
						else
							std::cout << pattern[i];
						if(frequencyWithOneTarget[i])
							std::cout << "(" << "ofreq:" << frequencyWithOneTarget[i] << ",rfreq:" << frequencyWithOneRootTarget[i] << ")";
						std::cout << " ";
					}
					std::cout << "(supp:" << m_frequency/(double)m_nbItems << ",conf:" << confidence << ",freq:" << m_frequency << ",nfreq:" << nodeWithoutTarget->m_frequency << ",id:" << m_nbSelected << ")" << std::endl;
				}
			}
		}
		// See other sibling
		if(isMainSibling)
			isMainSibling = false;
		else
			maximalSibling = maximalSibling->m_next;
	}
	// See alternatives
	if(m_alt)
		m_alt->output(length, pattern, leftIsMinimalHierarchy, leftIsMaximalHierarchy);
}

void Node::outputLevel(int level, int length, ITEMTYPE* pattern, bool outputAll){
	bool isMainSibling = true;
	ItemTypeList* maximalSibling = m_maximalSibling;
	while(isMainSibling || maximalSibling){
		pattern[length - 1] = isMainSibling ? m_itemType : maximalSibling->m_itemType;
		// See next nodes
		if(m_next && length < level)
			m_next->outputLevel(level, length + 1, pattern, outputAll);
		// Output current pattern
		if(outputAll || length == level)
			outputNodePattern(length, pattern);
		// See other sibling
		if(isMainSibling)
			isMainSibling = false;
		else
			maximalSibling = maximalSibling->m_next;
	}
	// See alternatives
	if(m_alt)
		m_alt->outputLevel(level, length, pattern, outputAll);
}

void Node::outputNodePattern(int length, ITEMTYPE* pattern){
	outputPattern(length, pattern);
	std::cout << "(freq:" << m_frequency << ",node:"<< this << ",segment:" << m_segmentLength << ")" << std::endl;
}

void Node::outputPattern(int length, ITEMTYPE* pattern){
	for(int i = 0; i < length; i++){
		outputItemType(pattern[i]);
		std::cout << ' ';
	}
}

void Node::outputItemType(ITEMTYPE itemType){
	if(m_translation)
		std::cout << m_translation[itemType];
	else
		std::cout << itemType;
}

