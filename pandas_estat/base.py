from abc import ABCMeta
from abc import abstractmethod
import re

import requests


class BaseReader(metaclass=ABCMeta):
    """
    Base class of all readers in `pandas-estat`.
    `StatsListReader` and `StatsDataReader` subclass this.

    Attributes
    ----------
    - query : str
        e-Stat API のリクエスト URL におけるクエリパラメータです。(参照: parameter `url`)
        例えば、統計表情報は `getSimpleStatsList`, 統計データは `getSimpleStatsList` です。
        参照: e-Stat API v3.0 仕様 2. API の利用方法
    - table_tag : str
        表データを示すタグ名です。
        例えば、統計表情報は `STAT_INF`, 統計データは `VALUE` です。
        参照: e-Stat API v3.0 仕様 4. API の出力データ

    References
    ----------
    e-Stat API v3.0 仕様
    https://www.e-stat.go.jp/api/sites/default/files/uploads/2019/07/API-specVer3.0.pdf
    """

    QUERY = NotImplemented
    TABLE_TAG = NotImplemented

    @property
    def url(self):
        """
        e-Stat API のリクエスト URL です。
        参照: e-Stat API v3.0 仕様 2. API の利用方法

        Returns
        -------
        - url : str
        """
        return f"https://api.e-stat.go.jp/rest/{self.version}/app/{self.QUERY}"

    @property
    @abstractmethod
    def params(self):
        """
        e-Stat API のパラメータ群を `dict` 形式で返します。
        参照: e-Stat API v3.0 仕様 2. API の利用方法, 3. API パラメータ

        Returns
        -------
        params : dict
        """

    @abstractmethod
    def read(self):
        """
        e-Stat API から表データを取得し、`pandas.DataFrame` 形式で返します。

        Returns
        -------
        dataframe : pandas.DataFrame
        """

    def get(self):
        """
        e-Stat API からレスポンスを GET し、`requests.Response` 形式で返します。

        Returns
        -------
        response : requests.Response
        """
        return requests.get(self.url, params=self.params)

    def _parse_response_text(self, text):
        """
        e-Stat API からのレスポンスのテキストをパースし、`dict` 形式で返します。
        表データのキーは `TABLE` とし、他の値のキーは e-Stat API のタグ名とします。
        参照: e-Stat API v3.0 仕様 4. API の出力データ

        Parameters
        ----------
        - text : str
            レスポンスのテキストです。

        Returns
        -------
        parsed_response_text : dict
            辞書にパースされたレスポンスのテキストです。
            キーの例は `TABLE`, `DATE`, `STATUS`, `ERROR_MSG` などです。
        """
        lines = text.splitlines()

        parsed = {}
        for i, line in enumerate(lines):
            match = re.match(r"\"([A-Z_]+)\",\"([^\"]+)\"", line)
            if match:
                key, value = match.group(1), match.group(2)
                parsed[key] = value
            elif line == f'"{self.TABLE_TAG}"':
                key, value = "TABLE", "\n".join(lines[i + 1 :])
                parsed[key] = value
                break

        return parsed
