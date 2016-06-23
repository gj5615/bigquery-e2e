#!/usr/bin/python2.7
## All rights to this package are hereby disclaimed and its contents
## released into the public domain by the authors.

'''Runs Python commands used in Chapter 7'''

import auth
import pprint
import time
project_id = 'hirenpatelatl-learn-bigquery'
service = auth.build_bq_client()
job_id = 'job_%d' % int(time.time() * 1000)
# Example 1 using jobs().query
		#response = service.jobs().query(
		#    projectId=project_id,
		#    body={'query': 'SELECT 17'}).execute()
		#pprint.pprint(response)
		#
# Example 2 using jobs().insert and then getting results from table_ref
	# 
	#response = service.jobs().insert(
	#    projectId = project_id,
	#    body={'configuration': {'query': {'query': 'SELECT 17'}},
	#          'jobReference': {'jobId': job_id, 'projectId': project_id}}
	#    ).execute()
	##pprint.pprint(response)

	#response = service.jobs().get(projectId=project_id, jobId=job_id).execute()

	#response = service.jobs().get(**response['jobReference']).execute()

	#pprint.pprint(response)

	#table_ref = response['configuration']['query']['destinationTable']
	#results = service.tabledata().list(**table_ref).execute()
	#pprint.pprint(results)
	#
	#schema = service.tables().get(**table_ref).execute()['schema']
	#pprint.pprint(schema)

# Example 3 execute query, identify destination table, display destination table id 
	#response = service.jobs().query(
	#    projectId=project_id,
	#    body={'query': 'SELECT 17', 'timeoutMs': 1000000}).execute()
	#pprint.pprint(response)

	#response = service.jobs().query(
	#    projectId=project_id,
	#    body={'query': 'SELECT 42'}).execute()
	#job = service.jobs().get(**response['jobReference']).execute()
	#destination_table=job['configuration']['query']['destinationTable']
	##pprint.pprint('tableId')
	#pprint.pprint(destination_table['tableId'])
	##
	#dataset = service.datasets().get(
	#    projectId=destination_table['projectId'],
	#    datasetId=destination_table['datasetId']).execute()
	#pprint.pprint('*********** service.datasets() **********')
	#pprint.pprint(dataset)
	#
	#table = service.tables().get(
	#    projectId=destination_table['projectId'],
	#    datasetId=destination_table['datasetId'],
	#    tableId=destination_table['tableId']).execute()
	#pprint.pprint('*********** service.tables() **********')
	#pprint.pprint(table)
# Example 4 
pprint.pprint('*********** service.query() query works of William Shakespeare publicdata:samples.shakespeare  **********')
query = 'SELECT COUNT(word), %f FROM [%s]' % (
    time.time(), 'publicdata:samples.shakespeare')
response1 = service.jobs().query(
    projectId=project_id,
    body={'query': query}).execute()
response2 = service.jobs().query(
    projectId=project_id,
    body={'query': query}).execute()
pprint.pprint(query)
pprint.pprint(response1)
# pprint.pprint(response2)

pprint.pprint('*********** service.query() query bigquery-e2e:reference.zip_codes  **********')
query = """
  SELECT state, COUNT(*) AS cnt 
  FROM [bigquery-e2e:reference.zip_codes] 
  WHERE population > 0 AND decommissioned = false 
  GROUP BY state, ORDER BY cnt DESC
"""
pprint.pprint(query)
pprint.pprint(
service.jobs().query(
    projectId=project_id,
    body={'query': query, 'useQueryCache': False}
    ).execute()['totalBytesProcessed']
)
pprint.pprint('*********** service.tables() scratch.cmd_20160306 filter numRows  **********')
pprint.pprint(
service.tables().get(
    projectId=project_id,
    datasetId='scratch',
    tableId='cmdhist_20160306').execute()['numRows']
)
cost_query = """
  SELECT state_len + pop_len + decommissioned_len FROM (
    SELECT SUM(LENGTH(state) + 2) AS state_len, 
      8 * COUNT(population) AS pop_len,
      COUNT(decommissioned) AS decommissioned_len
      FROM [bigquery-e2e:reference.zip_codes])
  """
pprint.pprint('*********** service.tables() bigquerye2e:reference.zip_codes cost to query state length **********')
pprint.pprint(
service.jobs().query(

    projectId=project_id,
    body={'query': cost_query}
    ).execute()['rows'][0]['f'][0]['v']
)
pprint.pprint('*********** service.tables() query dryrun **********')
pprint.pprint(
service.jobs().query(
    projectId=project_id,
    body={'query': query, 'dryRun': True}
    ).execute()['totalBytesProcessed']
)
