import duckdb
import pandas as pd

from algorithms.qcr.qcr import get_kc, get_c, create_sketch, hash_function, key_labeling, cross_product_tables
from utils.table_mapper import map_parts


def count_rows(df, only_shape=False):
    # Workaround to ensure correct inference of column types
    if only_shape:
        return pd.DataFrame({'count': [0]})
    return pd.DataFrame({'count': [len(df)]})


def callback_qcr(df_in: pd.DataFrame, only_shape=False) -> pd.DataFrame:
    if only_shape:
        df_out = pd.DataFrame(zip({"sample_term-1"}, {"sample_table_combination"}),
                              columns=['term_id', 'table_id_catcol_numcol'])
        return df_out  # Emtpy Dataframe and continuosly appending unadvised
    else:
        # df_out = pd.DataFrame(columns=['termid', 'table_id_catcol_numcol'])
        c_col = get_kc(df_in)
        c_col = get_kc(df_in)
        n_col = get_c(df_in)
        cross_product_tables_list = cross_product_tables(c_col, n_col, df_in.columns.name)
        list1, list2 = [], []
        for i in cross_product_tables_list:
            sketch = create_sketch(i.iloc[:, 0], i.iloc[:, 1], hash_function)
            labels = key_labeling(sketch)
            for term in labels:
                #list1.append(hash_function(term))
                list1.append(term)
                list2.append(i.columns.name)
                # df_out.append({'termid': term, 'table_id_catcol_numcol': i.columns.name})
        df_out = pd.DataFrame(zip(list1, list2), columns=['term_id', 'table_id_catcol_numcol'])
        return df_out


def main():
    con = duckdb.connect(':memory:')
    map_parts(con, 'result_table', '../data/zip_cache/', [  'abstraction_tables_licensed',
        'allegro_con_spirito_tables_licensed',
        'beats_per_minute_tables_licensed', 'cease_tables_licensed',
        'centripetal_acceleration_tables_licensed'
    ], callback_qcr)
    print(con.execute('SELECT * FROM result_table').fetchdf())
    print(con.execute('select term_id, count(*) as count from result_table group by term_id order by term_id').fetchdf())


if __name__ == "__main__":
    main()