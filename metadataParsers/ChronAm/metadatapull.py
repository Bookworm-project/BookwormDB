import urllib2, os, re, os.path, httplib, time, sys
from subprocess import Popen, list2cmdline, PIPE

PATH = "NewspaperFiles/"

def exec_commands(cmds):
    ''' Exec commands in parallel in multiple process 
    (as much as we have CPU)
    '''
    if not cmds: return # empty list

    def done(p):
        return p.poll() is not None
    def success(p):
        return p.returncode == 0
    def fail():
        sys.exit(1)

    max_task = 12
    processes = []
    while True:
        while cmds and len(processes) < max_task:
            task = cmds.pop()
            print list2cmdline(task)
            processes.append(Popen(task, stdout=PIPE))

        for p in processes:
            if done(p):
                if success(p):
                    processes.remove(p)
                else:
                    fail()

        if not processes and not cmds:
            break
        else:
            time.sleep(0.05)

# open the newspapers file
newspaper_file = open('newspapers.rdf', 'r')
newspapers = []
newspaper_list = newspaper_file.readlines()

for line in newspaper_list:
	phrases = re.findall(r'\w+', line)
	if 'about' in phrases:
		newspapers.append(phrases[5])
for newspaper in newspapers:
	if not os.path.isfile(PATH + newspaper + ".rdf"):
		issues = []
		try:
			newspaper_descfile = urllib2.urlopen(urllib2.Request('http://chroniclingamerica.loc.gov/lccn/' + newspaper + '.rdf'))
			newspaper_desc = newspaper_descfile.readlines()
		except:
			pass
		for line in newspaper_desc:
			desc_phrases = re.findall(r'\w+', line)
			if 'aggregates' in desc_phrases:
				issue_date = desc_phrases[6] + "-" + desc_phrases[7] + "-" + desc_phrases[8]
				issues.append(issue_date)
		for issue in issues:
			if not os.path.isfile(PATH + issue + '.rdf'):
				print issue
				'''
                                Looks to me like we're not getting the second editions of any papers if they have morning and afternoon--
				Might be worth looking in to.
                                '''
                                try:
					issuefile = urllib2.urlopen(urllib2.Request('http://chroniclingamerica.loc.gov/lccn/' + newspaper + '/' + issue + '/' + 'ed-1' + '.rdf'))
				except:
					pass
		
				issue_desc = issuefile.readlines()
				pages = []
				for line in issue_desc:
					issue_phrases = re.findall(r'\w+', line)
			
					if 'aggregates' in issue_phrases:
						pages.append(issue_phrases[12])
						print issue_phrases[12]
				commands = []
				for page in pages:
					page_dl = ['curl', '-o', PATH + newspaper + '_' + issue + '_' + page + '.txt', 'http://chroniclingamerica.loc.gov/lccn/' + newspaper + '/' + issue + '/' + 'ed-1' + '/' + 'seq-' + page + '/' + 'ocr.txt']
					commands.append(page_dl)
                                        ''' Blocking out the actual downloading for this script'''
				#exec_commands(commands)
			issue_out = open(PATH + newspaper + '_' + issue + '.rdf', 'w')
			for line in issuefile.readlines():
                            issue_out.write(line)
			issue_out.close()
		news_out = open(PATH + newspaper + '.rdf', 'w')
		news_out.write(newspaper_descfile.read())
		news_out.close()
