//
// Created by Sanqiang Zhao on 8/10/16.
//
#define MAX_STRING 100
#define EXP_TABLE_SIZE 1000
#define MAX_EXP 6
#define MAX_CODE_LENGTH 40

unsigned int
        layer1_size = 200, *negative_sampling_table, n_thread = 5, n_negative = 20;
char vector_file[MAX_STRING] =  "/Users/zhaosanqiang916/git/entity2vector/yelp_rest2/wordvector.txt",//"/home/sanqiang/data/glove/glove.twitter.27B.200d.txt"
pair_file[MAX_STRING] =  "/Users/zhaosanqiang916/git/entity2vector/yelp_rest2/pairentity.txt", //"/home/sanqiang/git/entity2vector/yelp_rest_allalphaword_yelp_mincnt10_win10/pairentity.txt",
        output_file[MAX_STRING] = "/Users/zhaosanqiang916/git/entity2vector/yelp_rest2/output/", // "/home/sanqiang/git/entity2vector/yelp_rest_allalphaword_yelp_mincnt10_win10/pairentity.txt",
        prod_file[MAX_STRING] = "/Users/zhaosanqiang916/git/entity2vector/yelp_rest2/user.txt"; // "/home/sanqiang/git/entity2vector/yelp_rest_allalphaword_yelp_mincnt10_win10/output.txt";
unsigned long long n_prod = 388525 /*24974 for prod entity*/, n_pair = 59751978, word_size = 60631;

const int table_size = 1e8;
const int vocab_hash_size = 30000000;