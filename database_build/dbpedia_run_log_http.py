from multiprocessing import Pool
import re, sys, requests, time, random, json
import numpy as np

from urlparse import urlparse, parse_qs
import urllib

fallback_json = { "head": { "link": [], "vars": ["property", "propertyLabel", "propertyVal", "propertyValLabel"] },
  "results": { "distinct": False, "ordered": True, "bindings": [ ] } }

def run_http_request(req):
	'''Executes HTTP request to server and returns time

	Keyword-args:
	req -- sparql query in url formatting
	'''
	url = 'http://claudio11.ifi.uzh.ch:8890' + req + '&timeout=20000&format=json'
	t0 = time.clock()
	# make call and measure time taken
	resp = requests.get(url)
	time1 = time.clock() - t0
	return resp, time1

def cleanup_query(query):
	'''Cleans log-url into readable sparql query

	Keyword-args:
	query -- log-url to clean
	'''
	line_no_tabs = re.sub(r'%09|%0B', '+', query)
	line_single_spaces = re.sub(r'\++', '+', line_no_tabs)
	line_no_formatting = re.sub(r'%0A|%0D', '', line_single_spaces)
	line_noprefix = re.sub(r'.*query=', '', line_no_formatting)
	line_noquotes = re.sub(r'"', '', line_noprefix)
	line_end_format = re.sub(r'(&.*?)$', '', line_noquotes)

	return urllib.unquote_plus(line_end_format.encode('ascii'))

def get_result_size(response):
	try:
		result_size = len(response['results']['bindings'])
	except:
		# respJson = fallback_json
		result_size = 0
	return result_size

def run_log(query_line):
	# open queries and regex for links
	url_ = re.findall('"GET (.*?) HTTP', query_line)

	if len(url_) == 1:
		request_url = url_[0]
		query_times = []
		resp = ''
		result_size = 0
		
		try:
			# use if warm execution times are needed
			for _ in range(11):
				response, exec_time = run_http_request(request_url)
				query_times.append(exec_time)
				# time.sleep(random.random()*2)
			
			respJson = response.json()
			result_size = get_result_size(respJson)
	
			# result_str = json.dumps(respJson['results']['bindings'])
			# result_str = result_str.replace('\t', ' ') #safety to safely read out results in file
			# result_str = result_str.replace('\n', ' ')
			# time.sleep(random.random()*2)
		except:
			exec_time = -1

		if exec_time != -1: #and result_size > 0:
			cold_exec_time = query_times[0]
			warm_times = query_times[1:]
			warm_mean = np.mean(warm_times, dtype=np.float64)

			query_clean = cleanup_query(request_url)
			return (query_clean + '\t' + str(warm_mean) + '\t' + str(cold_exec_time) + '\t' + str(result_size) + '\n')

def main():
	results = []
	# with open(log_file) as f:
	# 	#Spawn pool of workers to execute http queries
	# 	pool = Pool()
	# 	results = pool.map_async(run_log, f,1)
	# 	pool.close()
	# 	while not results.ready():
	# 		remaining = results._number_left
	# 		print "Waiting for", remaining, "tasks to complete..."
	# 		sys.stdout.flush()
	# 		time.sleep(10)
	count = 0
	with open('database.log') as in_:
		for l_ in in_:
			res = run_log(l_)
			if len(results) > 25000:
				break
			if res is not None:
				count +=1
				print ".%d." % (count)
				sys.stdout.flush()
				results.append(res)

	with open(log_file + '-ran', 'a') as out:
		for entry in results:
		# for entry in results.get():
			if entry is not None:
				out.write(str(entry))

if __name__ == '__main__':
	main()
