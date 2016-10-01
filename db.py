'''
Table:  ObjectType
   objectId         TEXT
   objectType       TEXT

Table:  IntObject
   objectId         TEXT
   objectValue      INTEGER

Table:  FloatObject
   objectId         TEXT
   objectValue      FLOAT

Table:  StringObject
   objectId         TEXT
   objectValue      TEXT

Table:  ListObject
   list_objectId    TEXT
   parentNodeId     TEXT
   
Table:  ListObjectMember
   list_objectId    TEXT
   member_objectId  TEXT
   list_position    FLOAT
'''