if True:
    execfile("/mnt/bschmidt/Internet_Archive/pyscripts/Pyfunctions.py")

 
if False:
    load_ngrams_word_list_as_new_sql_file() #Currently requires a text file with words and counts for import
    update_Porter_stemming()
    update_stopwords()
    create_catalog_table() #Works off a perl-created file not called by this script
    
if True: 
    execfile(project_directory+"/pyscripts/Pyfunctions.py")
        delete_matching_database_tables(libname)
        #run_R_library_creation_script(libname)
        create_counts_and_indexes(libname,mysql_directory)

