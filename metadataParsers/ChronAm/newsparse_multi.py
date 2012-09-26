import urllib2, os, re, os.path, httplib, time, sys
from subprocess import Popen, list2cmdline, PIPE

PATH = "../../../texts/raw/"
metadatapath = "../../../metadata/rdf/"

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

    max_task = 24
    processes = []
    while True:
        while cmds and len(processes) < max_task:
            task = cmds.pop()
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
            time.sleep(.1)

# open the newspapers file
newspaper_file = open('newspapers.rdf', 'r')
newspapers = []
newspaper_list = newspaper_file.readlines()

print "Getting list of papers"
for line in newspaper_list:
    phrases = re.findall(r'\w+', line)
    if 'about' in phrases:
        newspapers.append(phrases[5])
        
print "Beginning download series"
commands = []
for newspaper in newspapers:
    print "Starting newspaper" + newspaper
    if not os.path.isfile(metadatapath + newspaper + ".rdf"):
        issues = []
        try:
            newspaper_descfile = urllib2.urlopen(urllib2.Request('http://chroniclingamerica.loc.gov/lccn/' + newspaper + '.rdf'))
            newspaper_desc = newspaper_descfile.readlines()
        except:
            continue
        for line in newspaper_desc:
            desc_phrases = re.findall(r'\w+', line)
            if 'aggregates' in desc_phrases:
                issue_date = desc_phrases[6] + "-" + desc_phrases[7] + "-" + desc_phrases[8]
                issues.append(issue_date)
        for issue in issues:
            if not os.path.isfile(metadatapath + issue + '.rdf'):
                '''
                Looks to me like we're not getting the second editions of any papers if they have morning and afternoon--
                Might be worth looking in to.
                ---BMS
                '''
                try:
                    issuefile = urllib2.urlopen(urllib2.Request('http://chroniclingamerica.loc.gov/lccn/' + newspaper + '/' + issue + '/' + 'ed-1' + '.rdf'))
                except:
                    continue
                issue_desc = issuefile.readlines()
                pages = []
                for line in issue_desc:
                    issue_phrases = re.findall(r'\w+', line)
                    if 'aggregates' in issue_phrases:
                        pages.append(issue_phrases[12])
                        for page in pages:
                            if not os.path.exists(PATH + newspaper + '_' + issue + '_' + page + '.txt'):
                                page_dl = ['curl', '-so', PATH + newspaper + '_' + issue + '_' + page + '.txt', 'http://chroniclingamerica.loc.gov/lccn/' + newspaper + '/' + issue + '/' + 'ed-1' + '/' + 'seq-' + page + '/' + 'ocr.txt']
                                commands.append(page_dl) 
                #Once a big backlog is built up, start them downloading.
                if len(commands) >= 1000:
                    exec_commands(commands)
                    commands = []
                issue_out = open(metadatapath + "issues/" + newspaper + '_' + issue + '.rdf', 'w')
                issue_out.write("\n".join(issue_desc))
                issue_out.close()
        print "Downloading " + newspaper
        exec_commands(commands)
        commands = []
                
        print "writing file for " + newspaper
        news_out = open(metadatapath + newspaper + '.rdf', 'w')
        news_out.write("\n".join(newspaper_desc))
        news_out.close()
                    
#Clear the cache at the end.
exec_commands(commands)
