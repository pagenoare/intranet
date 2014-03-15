# -*- coding: utf-8 -*-
import colander

class TeamAddSchema(colander.MappingSchema):
    name = colander.SchemaNode(colander.String(), validator=colander.Length(1, 255))
    swap_with_preview = colander.SchemaNode(colander.Boolean(), missing=colander.drop)


class UsersSchema(colander.SequenceSchema):
    id = colander.SchemaNode(colander.Int())

   
class TeamUpdateSchema(colander.MappingSchema):
    name = colander.SchemaNode(colander.String(), validator=colander.Length(max=255), missing=None)
    users = UsersSchema(missing=colander.drop)
    swap_with_preview = colander.SchemaNode(colander.Boolean(), missing=colander.drop)
