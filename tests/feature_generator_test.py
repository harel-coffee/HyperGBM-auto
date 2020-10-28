# -*- coding:utf-8 -*-
"""

"""
import math
from datetime import datetime

import featuretools as ft
from featuretools.variable_types import Numeric, Categorical
import pandas as pd
import pytest
import numpy as np
from sklearn.model_selection import train_test_split
from tabular_toolbox.datasets import dsutils
from tabular_toolbox.sklearn_ex import FeatureSelectionTransformer
from hypergbm.feature_generators import FeatureToolsTransformer, CrossCategorical


class Test_FeatureGenerator():
    def test_char_add(self):
        x1 = ['1', '2']
        x2 = ['c', 'd']
        x3 = np.char.add(x1, x2)
        assert x3

    def test_ft_primitives(self):
        tps = ft.primitives.get_transform_primitives()
        assert tps

    def test_feature_tools_categorical_cross(self):
        df = dsutils.load_bank()
        df.drop(['id'], axis=1, inplace=True)
        cross_cat = CrossCategorical()
        X_train, X_test = train_test_split(df.head(100), test_size=0.2, random_state=42)
        ftt = FeatureToolsTransformer(trans_primitives=[cross_cat])
        ftt.fit(X_train)
        x_t = ftt.transform(X_train)
        assert len(set(x_t.columns.to_list()) - set(
            ['job', 'marital', 'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome', 'y', 'age',
             'balance', 'day', 'duration', 'campaign', 'pdays', 'previous', 'contact__marital', 'job__poutcome',
             'contact__default', 'housing__month', 'housing__marital', 'loan__y', 'housing__job', 'loan__poutcome',
             'month__poutcome', 'default__month', 'default__education', 'education__loan', 'education__housing',
             'housing__loan', 'housing__poutcome', 'contact__housing', 'contact__loan', 'marital__y', 'contact__job',
             'education__poutcome', 'default__marital', 'job__month', 'job__y', 'default__loan', 'education__marital',
             'default__poutcome', 'default__y', 'contact__month', 'education__month', 'contact__education',
             'contact__poutcome', 'job__marital', 'education__job', 'job__loan', 'contact__y', 'month__y',
             'default__housing', 'default__job', 'poutcome__y', 'loan__marital', 'education__y', 'loan__month',
             'marital__month', 'housing__y', 'marital__poutcome'])) == 0

    def test_feature_tools_transformer(self):
        df = dsutils.load_bank()
        df.drop(['id'], axis=1, inplace=True)
        X_train, X_test = train_test_split(df.head(100), test_size=0.2, random_state=42)
        ftt = FeatureToolsTransformer(trans_primitives=['add_numeric', 'divide_numeric'])
        ftt.fit(X_train)
        x_t = ftt.transform(X_train)
        assert x_t is not None

    def test_feature_selection(self):
        df = dsutils.load_bank().head(1000)
        df.drop(['id'], axis=1, inplace=True)
        y = df.pop('y')
        cross_cat = CrossCategorical()
        ftt = FeatureToolsTransformer(trans_primitives=['add_numeric', 'divide_numeric', cross_cat])
        ftt.fit(df)
        x_t = ftt.transform(df)

        fst = FeatureSelectionTransformer('classification', ratio_max_cols=0.2)
        fst.fit(x_t, y)
        assert len(fst.scores_.items()) == 115
        assert len(fst.columns_) == 23
        x_t2 = fst.transform(x_t)
        assert x_t2.shape[1] == 23

    @pytest.mark.parametrize('fix_input', [True, False])
    def test_fix_input(self, fix_input: bool):
        df = pd.DataFrame(data={"x1": [None, 2, 3], 'x2': [4, 5, 6]})

        ftt = FeatureToolsTransformer(trans_primitives=['add_numeric', 'divide_numeric'], fix_input=fix_input,
                                      fix_output=False)
        ftt.fit(df)
        x_t = ftt.transform(df)
        assert "x1 + x2" in x_t
        assert "x1 / x2" in x_t

        if fix_input is True:
            # should no NaN value not only input nor output
            assert not math.isnan(x_t["x1"][0])
            assert not math.isnan(x_t["x1 / x2"][0])
        else:
            # x1 is NaN, it's children is NaN too.
            assert math.isnan(x_t["x1"][0])
            assert math.isnan(x_t["x1 / x2"][0])

    @pytest.mark.parametrize('fix_output', [True, False])
    def test_fix_output(self, fix_output: bool):
        df = pd.DataFrame(data={"x1": [1, 2, 3], 'x2': [0, 5, 6]})
        ftt = FeatureToolsTransformer(trans_primitives=['add_numeric', 'divide_numeric'], fix_output=fix_output)
        ftt.fit(df)
        x_t = ftt.transform(df)
        assert "x1 + x2" in x_t
        assert "x1 / x2" in x_t

        if fix_output is True:
            assert not math.isinf(x_t["x1 / x2"][0])
        else:
            assert math.isinf(x_t["x1 / x2"][0])

    def test_datetime_derivation(self):

        df = pd.DataFrame(data={"x1": [datetime.now()]})
        ftt = FeatureToolsTransformer(trans_primitives=["year", "month", "week"])
        ftt.fit(df)

        x_t = ftt.transform(df)
        assert "YEAR(x1)" in x_t
        assert "MONTH(x1)" in x_t
        assert "WEEK(x1)" in x_t

    def test_persist(self, tmp_path: str):
        from os import path as P
        tmp_path = P.join(tmp_path, 'fft.pkl')

        df = pd.DataFrame(data={"x1": [datetime.now()]})
        ftt = FeatureToolsTransformer(trans_primitives=["year", "month", "week"])
        ftt.fit(df)
        import pickle

        with open(tmp_path, 'wb') as f:
            pickle.dump(ftt, f)

        with open(tmp_path, 'rb') as f:
            ftt1 = pickle.load(f)

        x_t = ftt1.transform(df)
        assert "YEAR(x1)" in x_t
        assert "MONTH(x1)" in x_t
        assert "WEEK(x1)" in x_t
