import pandas as pd
import utils

files_data="data/extract_scraping.xlsx"
coproducers_data='data/extract_scraping_coprod.xlsx'
out_file="data/projects_to_be_matched.xlsx"

def preprocessing(files_data,coproducers_data,out_file):
    ########################
    # Files list
    ########################
    files_df=pd.read_excel(files_data)

    # clean duplicates
    files_df=files_df.drop_duplicates()

    # fill na in director's first and last name and create the column Director
    files_df["Firstname"]=files_df["Firstname"].fillna('')
    files_df["Lastname"]=files_df["Lastname"].fillna('')
    files_df["Director"]=files_df["Firstname"]+' '+files_df["Lastname"]
    files_df=files_df.drop(columns=['Firstname','Lastname'])

    # assign correct types to columns
    # files_df.Reference=files_df.Reference.astype('string')
    # files_df.OriginalTitle=files_df.OriginalTitle.astype('string')
    # files_df.FrenchTitle=files_df.FrenchTitle.astype('string')
    # files_df.EnglishTitle=files_df.EnglishTitle.astype('string')
    # files_df.CommitteDecisionDate=pd.to_datetime(files_df.CommitteDecisionDate)
    # files_df.kind=files_df.kind.astype('string')
    # files_df.Genre=files_df.Genre.astype('string')
    # files_df.support=files_df.support.astype('string')
    # files_df.SecretariatDecision=files_df.SecretariatDecision.astype('string')
    # files_df.budget=pd.to_numeric(files_df.budget)
    # files_df.reason=files_df.reason.astype('string')
    # files_df.Director=files_df.Director.astype('string')


    # group by projects (directors now will contain lists of director names)
    columns_grp=files_df.columns.to_list()
    columns_grp.remove("Director")
    grouped = files_df.groupby(columns_grp,dropna=False)
    files_df_grp = grouped.agg(list).reset_index()
    files_df_grp.Director=files_df_grp.Director.apply(lambda x : list(set(x))) #removes the names duplicated in the same project


    ########################
    # Coproducers list
    ########################
    prod_df=pd.read_excel(coproducers_data,usecols=["ID",'CoproducerId', 'country1','countryname1_english','AnnouncedAmount','percentage_participation', 'contributor_rank','majmin'])
    # group by projects
    grouped=prod_df.groupby(by=["ID"],dropna=False)
    prod_df_grp=grouped.agg(list).reset_index()
    prod_df_grp



    ################################################
    # join Files list and Coproducers list
    ################################################
    join_df=files_df_grp.assign(key=files_df_grp.ID).merge(prod_df_grp.assign(key=prod_df_grp.ID),on='key',how='left')


    # remove duplicate columns
    join_df=join_df.drop(['ID_y'],axis=1)
    #and rename the remaining ones
    join_df=join_df.rename(columns={"ID_x": "ID"})



    ########################
    # some cleaning
    ########################
        
    for col in ['OriginalTitle', 'FrenchTitle','EnglishTitle',]:
        join_df.loc[:,col]=join_df.loc[:,col].apply(utils.remove_unnecessary_spaces)

    for col in ['OriginalTitle', 'FrenchTitle','EnglishTitle', 'CommitteDecisionDate', 'kind', 'Genre', 'support',
        'SecretariatDecision', 'firstfilm', 'secondfilm', 'budget', 'reason',
        'Director']:
        join_df.loc[:,col]=join_df.loc[:,col].apply(utils.remove_empty)

    # removes the project that are cancelled
    join_df=join_df.loc[join_df["reason"].isna(),:]
    join_df=join_df.reset_index(drop=True)

    if "level_0" in join_df.keys():
        del join_df["level_0"]


    join_df.to_excel(out_file,index=None)

    return join_df