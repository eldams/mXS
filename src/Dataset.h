class Dataset {
	public:
		Dataset(char*);
		~Dataset();
		Transaction* getTransactions();
		ITEMTYPE getMaximumItemType();
		int getNbItems();
		void setRootTarget(ITEMTYPE);
		ITEMTYPE getRootTarget();
		void setHierarchy(char*);
		ItemTypeList** getHierarchy();
		void setTransactionsTarget();
		void setTranslation(char*);
		char** getTranslation();
	private:
		Transaction* m_transactions;
		ITEMTYPE m_maximumItemType;
		int m_nbItems;
		ITEMTYPE m_rootTarget;
		ItemTypeList** m_hierarchy;
		char** m_translation;
		void setTransactions(char*);
		Transaction* readTransactionLine(char*);
		ItemTypeList* readHierarchyLine(char*);
};

