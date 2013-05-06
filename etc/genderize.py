

class Genderizer:
    def __init__(self):
        pass
        #This will be dropped in elsewhere

    def checkName(self,name,year=1990,host="melville.seas.harvard.edu"):
        import urllib
        destination = "http://" + host + "/cgi-bin/genderizer.py"
        params = {'name':name,'year':year}
        encoded_params = urllib.urlencode(params)
        
        destination = destination + '?' + encoded_params
        print destination
        response = urllib.urlopen(destination)
        femaleProb = float(response.read())
        if femaleProb < .05:
            return "Male"
        elif femaleProb > .95:
            return "Female"
        else:
            return "NA"
        
