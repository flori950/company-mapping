CRUNCHBASE_QUERY = {
  "field_ids": [
        "name",
        "created_at",
        "entity_def_id",
        "facebook",
        "facet_ids",
        "identifier",
        "image_id",
        "image_url",
        "linkedin",
        "location_identifiers",
        "permalink",
        "short_description",
        "stock_exchange_symbol",
        "twitter",
        "updated_at",
        "uuid",
        "website_url",
        "rank_org"
  ],
  "order": [
    {
      "field_id": "rank_org",
      "sort": "asc"
    }
  ],
  "query": [
    {
      "type": "predicate",
      "field_id": "location_identifiers",
      "operator_id": "includes",
      "values": [
       "6085b4bf-b18a-1763-a04e-fdde3f6aba94"
      ]
    }
  ],
}
# "6106f5dc-823e-5da8-40d7-51612c0b2c4e" -> europe
# "6085b4bf-b18a-1763-a04e-fdde3f6aba94" -> germany