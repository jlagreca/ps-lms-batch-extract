#!/usr/bin/env python
# coding=utf-8

import json
import sys
from lxml import etree

from pslms.base import LMSObject


class PS2Couch(LMSObject):

	def argument_parser(self):
		parser = super(PS2Couch, self).argument_parser()

		parser.add_argument('file', help='Path to XML file with IMS Enterprise data')
		parser.add_argument('element', help='The entity element name in the incoming XML data')
		parser.add_argument('type', help='The type to use in stored JSON documents')
		parser.add_argument('db', help='CouchDB connection name')

		return parser

	def main(self):
		process_f = self.process_membership_doc if self.args.element == 'membership' else self.process_doc
		target_db = self.couchdb_client(self.args.db)
		context = etree.iterparse(self.args.file, events=('end',), tag=self.args.element)

		for event, elem in context:
			doc = self.etree_to_dict(elem)
			process_f(doc, target_db)

	def doc_with_extracted_id(self, doc):
		doc_id = doc.get('sourcedid', {}).get('id')

		if doc_id:
			doc['_id'] = doc_id

		return doc

	def process_doc(self, doc, target_db):
		doc = self.doc_with_extracted_id(doc)
		if not '_id' in doc:
			return
		doc['type'] = self.args.type
		target_db.update_doc('lms/from_ps', docid=doc['_id'], body=doc)

	def process_membership_doc(self, doc, target_db):
		# Memberships are further broken down by member
		print doc['sourcedid']['id']
		membership_sourcedid = doc['sourcedid']
		membership_id = membership_sourcedid['id']
		members = (doc['member'],) if isinstance(doc['member'], dict) else doc['member']
		for member in members:
			member['_id'] = membership_id + '-' + member['sourcedid']['id']
			member['membership_sourcedid'] = membership_sourcedid
			member['type'] = self.args.type
			target_db.update_doc('lms/from_ps', docid=member['_id'], body=member)

	def _is_sequence(self, arg):
		return (not hasattr(arg, "strip") and
						hasattr(arg, "__getitem__") or
						hasattr(arg, "__iter__"))


def main(args=None):
	PS2Couch(
		args = args,
		connection_info = {
			'lms_data': {
				'url': 'http://127.0.0.1:5984/lms-data'
			}
		}
	).run()

def people_main():
	args = sys.argv[1:]
	args.extend(['person', 'person', 'lms_data'])
	main(args)

def membership_main():
	args = sys.argv[1:]
	args.extend(['membership', 'member', 'lms_data'])
	main(args)

def group_main():
	args = sys.argv[1:]
	args.extend(['group', 'course', 'lms_data'])
	main(args)

if __name__ == '__main__':
	main()

