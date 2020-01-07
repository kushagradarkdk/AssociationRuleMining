import pandas as pd
import itertools
from collections import defaultdict

from click._compat import raw_input

USED_ROWS = 100000


class Apriori:
    def __init__(self,order_file,product_file,min_support=0.01,min_confidence=0.01):

        self.order_file = order_file
        self.product_file = product_file
        self.support_threashold = min_support
        self.confidence_threashold = min_confidence
        self.total_transactions = None
        self.processed_product_names = None
        self.single_item_freq_table = None
        self.product_order_dict = None

        self.preprocess_data()


    # Method to get support of a product
    def getSupport(self,product_freq):
        return (product_freq/self.total_transactions >= self.support_threashold),product_freq/self.total_transactions

    # Method to get confidence of a product and check with threshold
    def CheckConfidence(self,pair_support,item_support):
        return pair_support/item_support >= self.confidence_threashold,pair_support/item_support

    def generate_k_itemSet(self,itemset,k):
        itemset.sort()
        result = []
        return_result = []
        length = len(itemset)
        for i in range(0, length):
            for j in range(i + 1, length):
                listing1 = itemset[i]
                listing2 = itemset[j]
                listing1.sort()
                listing2.sort()
                if listing1 != listing2:
                    result.append(listing1 + list(set(listing2) - set(listing1)))
        hset = set(tuple(row) for row in result)
        temp = [list(item) for item in hset]
        for item in temp:
            # print(item)
            if len(item) == k:
                return_result.append(item)

        return return_result

    # Method to get the frequency of the products
    def freq_1_itemset(self):
        output_list_k_1 = []
        for product in self.single_item_freq_table:
            # Calculate support and
            item_support_status,item_support = self.getSupport(self.single_item_freq_table[product])
            if item_support_status:
                # list = []
                # list.append(product)
                output_list_k_1.append([product])
        return output_list_k_1

    def Generate_All_Frequent_Itemsets(self):
        k = 1
        # Apply support threashold value for frequent item dataset 1
        item_set = self.freq_1_itemset()
        resultant_k_itemsets = []
        while k < 2:
            # generated_freq_k_itemset = []
            # Get all combinations for item_set list with number of items per combination = k+1
            k += 1
            k_itemset = self.generate_k_itemSet(itemset=item_set,k=k)

            for item in k_itemset:
                generated_freq_k_itemset = []
                item_count = 0
                set_items = set(item)

                for order_data in self.processed_product_names:
                    if set_items.issubset(order_data) == True:
                        item_count += 1

                # Remove items based on the support threshold
                item_support_status,item_support = self.getSupport(item_count)
                if item_support_status:
                    item.sort()
                    generated_freq_k_itemset.append([item,item_support])

                if len(generated_freq_k_itemset) != 0:
                    item_set = []
                    # Updating itemset with newly generated k item set vals
                    item_set = generated_freq_k_itemset
                    resultant_k_itemsets.append(generated_freq_k_itemset)

        return resultant_k_itemsets

    def print_baggageContent(self, association_dict, baggage):
        print("Items added to baggage : ")
        print(baggage)
        choice = raw_input("Do you want to add more items ? Press Y for Yes or N for Checkout \n")
        if (choice == 'Y' or choice == 'y'):
            self.recommend_items(association_dict, baggage)
        else:
            print("Thank You for shopping with us.")

    def recommend_items(self, association_dict, bag=[]):
        baggage = bag
        while True:
            chosen_item = raw_input("Please choose an item you want to buy and if Not press 'Q' to quit\n")
            if (chosen_item == 'Q'):
                break
            else:
                if chosen_item in association_dict:
                    print("These items are bought together often. Do you want any of these ?")
                    print(association_dict[chosen_item])
                    baggage.append(chosen_item)
                else:
                    print("%s not found" % (chosen_item))
        self.print_baggageContent(association_dict, baggage)


    def Generate_Assosiation_Rules(self):
        print("Assosiation Rules")
        print("-----------------")
        print("RULES \t\t SUPPORT \t\t CONFIDENCE")
        k_2_itemsets = self.Generate_All_Frequent_Itemsets()
        association_dict = dict()
        subset_size = 1 # size of of the subsets
        num = 1
        for pair_list in k_2_itemsets:
            for pair in pair_list:
                data = pair[:-1]
                for item in data:
                    data = item
                subset = set(itertools.combinations(data,subset_size))
                pair_support = pair[-1]

                for item in subset:
                    item_count = 0
                    item = set(item)
                    for order_data in self.processed_product_names:
                        if item.issubset(order_data):
                            item_count += 1

                    item_support_status, item_support = self.getSupport(item_count)

                    # Check confidence threshold
                    pair_confidence_status,pair_confidence =  self.CheckConfidence(pair_support,item_support)
                    if pair_confidence_status:
                        for i in data:
                            if i not in item:
                                product = i

                        item = list(item)
                        if item[0] in association_dict:
                            l = association_dict.get(item[0])
                            l.append(product)
                        else:
                            association_dict[item[0]] = [product]
                        print("Rule#  %d : %s ==> %s %f %f" % (num, item, [product], item_support, pair_confidence))
                        num += 1
        baggage = []
        self.recommend_items(association_dict, baggage)
    """
    Preprocessing Input data
    """
    def preprocess_data(self):
        orders = pd.read_csv(self.order_file)
        products = pd.read_csv(self.product_file)

        # Generate list of order_id and product_id from the orders
        condensed_order = orders[['order_id', 'product_id']]

        #Generate list of product_id and product_name from the products
        products = products[['product_id','product_name']]
        products_indexID = products.set_index('product_id')['product_name']

        orDict = defaultdict(list)

        #  Dictionary for order_id vs list of products
        for index, row in condensed_order.head(n=USED_ROWS).iterrows():
            orDict[row[0]].append(products_indexID[row[1]].replace(" ",""))

        transactions = 0
        #Compute candidate 1-itemset
        item_freq = {}
        processed_product_names = []
        for key,value in orDict.items():
            temp = []
            transactions +=1
            for word in value:
                word = word.replace(" ","")
                temp.append(word)
                # Generating a dictionary with item vs its frequency
                if word not in item_freq.keys():
                    item_freq[word] = 1
                else:
                    item_freq[word] += 1
            processed_product_names.append(temp)

        self.total_transactions = transactions
        self.processed_product_names = [set(transaction_items) for transaction_items in processed_product_names]
        self.single_item_freq_table = item_freq
        self.product_order_dict = orDict

if __name__ == "__main__":
    MIN_SUPPORT_IN_PERCENT = 1
    MIN_CONFIDENCE_IN_PERCENT = 10

    # Apriori Class
    association_rules = Apriori(order_file='https://personal.utdallas.edu/~kxd180025/order_products__train.csv',product_file='https://personal.utdallas.edu/~kxd180025/products.csv',min_support=MIN_SUPPORT_IN_PERCENT/100,min_confidence=MIN_CONFIDENCE_IN_PERCENT/100)
    association_rules.Generate_Assosiation_Rules()