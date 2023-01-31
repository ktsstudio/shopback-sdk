from typing import Optional

import os
from dataclasses import dataclass, field

import requests
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


@dataclass
class ProductData:
    project_id: int
    category_name: str
    name: str
    description: str
    price: float
    attachment_ids: list[int]
    external_id: Optional[str] = None
    category_external_id: Optional[str] = None


@dataclass
class ModificationData:
    parent_id: int
    external_id: str
    price: float
    name: str = ""  # если оставить пустую строку - имя будет взято из родительского продукта
    description: Optional[
        str
    ] = ""  # если оставить пустую строку или none - описание будет взято из родительского продукта
    attachment_ids: list[int] = field(default_factory=list)


@dataclass
class OptionsData:
    product_id: int
    size_option: Optional[str] = None
    color_option: Optional[str] = None
    addon_ids: Optional[list[int]] = None


@dataclass
class CategoryData:
    project_id: int
    name: str
    external_id: str
    attachment: Optional[int] = None
    parent_external_id: Optional[int] = None


class OldClientSDK:
    DEFAULT_URL = "https://shopback.ru-prod2.kts.studio"

    def __init__(self, session_id: str, url: Optional[str] = None) -> None:
        self.url = url or self.DEFAULT_URL
        self.session_id = session_id
        t = RequestsHTTPTransport(self.graphql_url, headers=self.session_cookies)
        self.client = Client(transport=t, fetch_schema_from_transport=True)

    @property
    def graphql_url(self) -> str:
        return self.url + "/graphql"

    @property
    def upload_url(self) -> str:
        return self.graphql_url + "/attachment/upload"

    @property
    def session_cookies(self) -> dict:
        return {"Cookie": f"sessionid={self.session_id}"}

    def upload_files(self, paths: list[str]) -> list[int]:
        res = []
        files = [
            ("file", (os.path.basename(item), open(item, mode="rb"), "image/*")) for item in paths
        ]
        response = requests.post(self.upload_url, headers=self.session_cookies, files=files)
        if response.status_code == 200:
            data = response.json()["data"]
            res += [item["aid"] for item in data]
        return res

    def upload_urls(self, urls: list[str]) -> list[Optional[int]]:
        res: list[Optional[int]] = []
        for url in urls:
            r = requests.get(url, allow_redirects=False)
            if r.status_code != 200:
                res.append(None)
                continue
            name = url.split("/")[-1]
            files = [("file", (name, r.content, "image/*"))]
            response = requests.post(self.upload_url, headers=self.session_cookies, files=files)
            if response.status_code == 200:
                data = response.json()["data"]
                res += [item["aid"] for item in data]
        return res

    def upload_product(self, product: ProductData) -> dict:
        query = gql(
            """
            mutation product(
              $project: String!,
              $categoryName: String!,
              $categoryExternalId: String,
              $externalId: String,
              $name: String!,
              $description: String!,
              $price: Decimal!,
              $attachments: [Int]!
            ) {
              product(input: {
                name: $name,
                externalId: $externalId,
                project: $project,
                description: $description,
                price: $price,
                categoryName: $categoryName,
                categoryExternalId: $categoryExternalId,
                attachments: $attachments}
              ) {
                data {id},
                errors {status, message, fieldProblems {fieldName, errDescription}}
              }
            }
        """
        )
        params = {
            "name": product.name,
            "externalId": product.external_id,
            "project": str(product.project_id),
            "description": product.description,
            "price": product.price,
            "categoryName": product.category_name,
            "categoryExternalId": product.category_external_id,
            "attachments": product.attachment_ids,
        }
        result = self.client.execute(query, variable_values=params)
        return result

    def upload_product_and_return_id(self, product: ProductData) -> int:
        res = self.upload_product(product)
        product_id = res["product"]["data"]["id"]
        product_id = int(product_id)
        return product_id

    def upload_modification(self, mod: ModificationData) -> dict:
        query = gql(
            """
            mutation modification(
              $parent: String!,
              $externalId: String!,
              $name: String!,
              $description: String,
              $price: Decimal!,
              $attachments: [Int]
            ) {
              modification(input: {
                parent: $parent,
                externalId: $externalId,
                name: $name,
                description: $description,
                price: $price,
                attachments: $attachments}
              ) {
                data {id},
                errors {status, message, fieldProblems {fieldName, errDescription}}
              }
            }
        """
        )
        params = {
            "parent": str(mod.parent_id),
            "externalId": mod.external_id,
            "name": mod.name,
            "description": mod.description,
            "price": mod.price,
            "attachments": mod.attachment_ids,
        }
        result = self.client.execute(query, variable_values=params)
        return result

    def upload_modification_and_return_id(self, mod: ModificationData) -> int:
        res = self.upload_modification(mod)
        mod_id = res["modification"]["data"]["id"]
        mod_id = int(mod_id)
        return mod_id

    def upload_options(self, options: OptionsData) -> dict:
        query = gql(
            """
            mutation productOptions(
              $product: Int!,
              $size_option: String,
              $color_option: String,
              $addon_ids: [Int!]
            ) {
              productOptions(input: {
                product: $product,
                sizeOption: $size_option,
                colorOption: $color_option,
                addonIds: $addon_ids
              }) {
                data {id, productOptions {color {key}, size {key}}},
                errors {status, message, fieldProblems {fieldName, errDescription}}
              }
            }
        """
        )
        params = {
            "product": options.product_id,
            "size_option": options.size_option,
            "color_option": options.color_option,
            "addon_ids": options.addon_ids,
        }
        result = self.client.execute(query, variable_values=params)
        return result

    def upload_category(self, category: CategoryData) -> dict:
        query = gql(
            """
            mutation category(
                $project: String!,
                $name: String,
                $externalId: String!,
                $attachment: String,
                $parentExternalId: String
            ) {
              category(input: {
                project: $project,
                name: $name,
                externalId: $externalId,
                attachment: $attachment,
                parentExternalId: $parentExternalId
              }) {
                data {
                  id
                },
                errors {status, message, fieldProblems {fieldName, errDescription}}
              }
            }
        """
        )
        params = {
            "project": str(category.project_id),
            "name": category.name,
            "externalId": category.external_id,
            "attachment": str(category.attachment) if category.attachment else "",
            "parentExternalId": category.parent_external_id or "",
        }
        result = self.client.execute(query, variable_values=params)
        return result
