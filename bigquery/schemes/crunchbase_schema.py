from . import schema_helpers as sh

CRUNCHBASE_SCHEMA = [
sh.DateTimeField("dwh_partitiondate"),
sh.StringField('Name'),
sh.StringField('Creation_Date'),
sh.StringField('Entity_Type'),
sh.StringField('Facebook_Link'),
sh.StringField('Facet_IDs'),
sh.StringField('Identifier'),
sh.StringField('Image_ID'),
sh.StringField('Image_URL'),
sh.StringField('LinkedIn_Link'),
sh.StringField('Permalink'),
sh.StringField('Short_Description'),
sh.StringField('Stock_Exchange_Symbol'),
sh.StringField('Twitter_Link'),
sh.StringField('Updated_Date'),
sh.StringField('UUID'),
sh.StringField('Website_URL'),
sh.StringField('City'),
sh.StringField('Region'),
sh.StringField('Country'),
sh.StringField('Continent')

]
