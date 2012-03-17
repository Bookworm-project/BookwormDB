##  Script for parsing arxiv metadata.  Call with a catalog file
##  that lists the bookids and file location (with _ for /) of the
##  abstracts:
##          awk -f parse_metadata.awk texts/catalog.txt
##
##  The code in the BEGIN statement sets up hashes for convenience.  "a"
##  is used to make the date into proper datetime SQL format.  "b" is to
##  translate the raw categories into ones that we will use in our database
BEGIN{
  a["Jan"] = "01"; 
  a["Feb"] = "02";
  a["Mar"] = "03";
  a["Apr"] = "04";
  a["May"] = "05";
  a["Jun"] = "06";
  a["Jul"] = "07";
  a["Aug"] = "08";
  a["Sep"] = "09";
  a["Oct"] = "10";
  a["Nov"] = "11";
  a["Dec"] = "12"; 
  OFS = "\t";
  where=0;  

  b["acc-phys"]="physics"
  b["adap-org"]="nlin"
  b["alg-geom"]="math"
  b["ao-sci"]="physics"
  b["astro-ph"]="physics.astro-ph"
  b["astro-ph.CO"]="physics.astro-ph"
  b["astro-ph.EP"]="physics.astro-ph"
  b["astro-ph.GA"]="physics.astro-ph"
  b["astro-ph.HE"]="physics.astro-ph"
  b["astro-ph.IM"]="physics.astro-ph"
  b["astro-ph.SR"]="physics.astro-ph"
  b["atom-ph"]="physics"
  b["bayes-an"]="physics"
  b["chao-dyn"]="nlin"
  b["chem-ph"]="physics"
  b["cmp-lg"]="cs"
  b["comp-gas"]="nlin"
  b["cond-mat"]="physics.cond-mat"
  b["cond-mat.dis-nn"]="physics.cond-mat"
  b["cond-mat.mes-hall"]="physics.cond-mat"
  b["cond-mat.mtrl-sci"]="physics.cond-mat"
  b["cond-mat.other"]="physics.cond-mat"
  b["cond-mat.quant-gas"]="physics.cond-mat"
  b["cond-mat.soft"]="physics.cond-mat"
  b["cond-mat.stat-mech"]="physics.cond-mat"
  b["cond-mat.str-el"]="physics.cond-mat"
  b["cond-mat.supr-con"]="physics.cond-mat"
  b["cs.AI"]="cs"
  b["cs.AR"]="cs"
  b["cs.CC"]="cs"
  b["cs.CE"]="cs"
  b["cs.CG"]="cs"
  b["cs.CL"]="cs"
  b["cs.CR"]="cs"
  b["cs.CV"]="cs"
  b["cs.CY"]="cs"
  b["cs.DB"]="cs"
  b["cs.DC"]="cs"
  b["cs.DL"]="cs"
  b["cs.DM"]="cs"
  b["cs.DS"]="cs"
  b["cs.ET"]="cs"
  b["cs.FL"]="cs"
  b["cs.GL"]="cs"
  b["cs.GR"]="cs"
  b["cs.GT"]="cs"
  b["cs.HC"]="cs"
  b["cs.IR"]="cs"
  b["cs.IT"]="cs"
  b["cs.LG"]="cs"
  b["cs.LO"]="cs"
  b["cs.MA"]="cs"
  b["cs.MM"]="cs"
  b["cs.MS"]="cs"
  b["cs.NA"]="cs"
  b["cs.NE"]="cs"
  b["cs.NI"]="cs"
  b["cs.OH"]="cs"
  b["cs.OS"]="cs"
  b["cs.PF"]="cs"
  b["cs.PL"]="cs"
  b["cs.RO"]="cs"
  b["cs.SC"]="cs"
  b["cs.SD"]="cs"
  b["cs.SE"]="cs"
  b["cs.SI"]="cs"
  b["cs.SY"]="cs"
  b["dg-ga"]="math"
  b["funct-an"]="math"
  b["gr-qc"]="physics.gr-qc"
  b["hep-ex"]="physics.hep-ex"
  b["hep-lat"]="physics.hep-lat"
  b["hep-ph"]="physics.hep-ph"
  b["hep-th"]="physics.hep-th"
  b["math.AC"]="math"
  b["math.AG"]="math"
  b["math.AP"]="math"
  b["math.AT"]="math"
  b["math.CA"]="math"
  b["math.CO"]="math"
  b["math.CT"]="math"
  b["math.CV"]="math"
  b["math.DG"]="math"
  b["math.DS"]="math"
  b["math.FA"]="math"
  b["math.GM"]="math"
  b["math.GN"]="math"
  b["math.GR"]="math"
  b["math.GT"]="math"
  b["math.HO"]="math"
  b["math.IT"]="math"
  b["math.KT"]="math"
  b["math.LO"]="math"
  b["math.MG"]="math"
  b["math.MP"]="math"
  b["math.NA"]="math"
  b["math.NT"]="math"
  b["math.OA"]="math"
  b["math.OC"]="math"
  b["math-ph"]="math.math-ph"
  b["math.PR"]="math"
  b["math.QA"]="math"
  b["math.RA"]="math"
  b["math.RT"]="math"
  b["math.SG"]="math"
  b["math.SP"]="math"
  b["math.ST"]="math"
  b["mtrl-th"]="physics.cond-mat"
  b["nlin.AO"]="nlin"
  b["nlin.CD"]="nlin"
  b["nlin.CG"]="nlin"
  b["nlin.PS"]="nlin"
  b["nlin.SI"]="nlin"
  b["nucl-ex"]="physics.nucl-ex"
  b["nucl-th"]="physics.nucl-th"
  b["patt-sol"]="nlin"
  b["physics.acc-ph"]="physics"
  b["physics.ao-ph"]="physics"
  b["physics.atm-clus"]="physics"
  b["physics.atom-ph"]="physics"
  b["physics.bio-ph"]="physics"
  b["physics.chem-ph"]="physics"
  b["physics.class-ph"]="physics"
  b["physics.comp-ph"]="physics"
  b["physics.data-an"]="physics"
  b["physics.ed-ph"]="physics"
  b["physics.flu-dyn"]="physics"
  b["physics.gen-ph"]="physics"
  b["physics.geo-ph"]="physics"
  b["physics.hist-ph"]="physics"
  b["physics.ins-det"]="physics"
  b["physics.med-ph"]="physics"
  b["physics.optics"]="physics"
  b["physics.plasm-ph"]="physics"
  b["physics.pop-ph"]="physics"
  b["physics.soc-ph"]="physics"
  b["physics.space-ph"]="physics"
  b["plasm-ph"]="physics"
  b["q-alg"]="math"
  b["q-bio.BM"]="q-bio"
  b["q-bio.CB"]="q-bio"
  b["q-bio.GN"]="q-bio"
  b["q-bio.MN"]="q-bio"
  b["q-bio.NC"]="q-bio"
  b["q-bio.OT"]="q-bio"
  b["q-bio.PE"]="q-bio"
  b["q-bio.QM"]="q-bio"
  b["q-bio"]="q-bio"
  b["q-bio.SC"]="q-bio"
  b["q-bio.TO"]="q-bio"
  b["q-fin.CP"]="q-fin"
  b["q-fin.GN"]="q-fin"
  b["q-fin.PM"]="q-fin"
  b["q-fin.PR"]="q-fin"
  b["q-fin.RM"]="q-fin"
  b["q-fin.ST"]="q-fin"
  b["q-fin.TR"]="q-fin"
  b["quant-ph"]="physics.quant-ph"
  b["solv-int"]="nlin"
  b["stat.AP"]="stat"
  b["stat.CO"]="stat"
  b["stat.ME"]="stat"
  b["stat.ML"]="stat"
  b["stat.OT"]="stat"
  b["stat.TH"]="stat"
  b["supr-con"]="physics.cond-mat"
}
{
  # x is the book id
  x = $1;

  # fn is the filename
  fn = $2;
  gsub(/_/,"/", fn);
  fn = "abs/"fn".abs"

  # where is used to deal with multiline author and title fields
  # t is title, au is author, c is the categories, fields is the line
  # we read in 
  where = 0;
  t = "";
  au = "";
  delete c;
  delete fields;
  while ((getline line < fn) > 0) {
    len=split(line, fields);
    # arxiv id
    if (line ~ /^arXiv:/) {
      id=substr(line,7);
    }
    # email address
    if (line ~ /^From:/) {
      from=substr(line,7);
      # take only the email address, not user name
      st=index(from, "<");
      ed=index(from, ">");
      from2=substr(from,st+1,ed-st-1);
      # take only the domain from the email address
      at=index(from2, "@");
      from=substr(from2, at+1);
      num=split(from, s, "\\.");
      final=s[num];
      # write out the domain levels separated by tabs.
      # the first level is "edu", then "harvard.edu", then "seas.harvard.edu"
      for (i=num-1; i>=1; i--) {
        dl=sprintf("%s", s[i]);
        for (j=i+1; j<=num; j++) {
	  dl=sprintf("%s.%s", dl,s[j]); 
        }
        final=sprintf("%s\t%s",final,dl);
      }
    }
    # date, convert to datetime format
    if (line ~ /^Date:/) {
      ds=sprintf("%s-%s-%02d %s",fields[5],a[fields[4]],fields[3],fields[6])
    }
    # where is for dealing with multiline title
    if (line ~ /^Title:/) {
      t=substr(line, index(line,fields[2]));
      where=1;
    }
    # where is for dealing with multiline author
    if (line ~ /^Authors:/) {
      au=substr(line, index(line,fields[2]));
      where=2;
    }
    # if line starts with an indentation, choose appropriate field to add to
    if (line ~ /^  /) {
      if (where==1)
	t=t""line;
      else if (where==2) 
	au=au""line;
    }
    # reset where if we get to end of metadata
    if (line ~ /^\\/) {
      where=0;
    }
    # reset where if we get to Categories, which is always after title/author
    if (line ~ /^Categories:/) {
      where = 0;
      # loop over all categories
      for (i=2; i<=len; i++) {
	# check if we already saw it; want to preserve original order
        if (!(fields[i] in c)) {
	  # check if it's a funky one
	  if (fields[i] in b) {
	    # b-mapped category not seen yet, add
	    if (!(b[fields[i]] in c)) {
	      c[b[fields[i]]]=i;
	      print x,id,ds,t,au,b[fields[i]], final;
	    }
	  }
	  else {
	    # regular category not seen yet, add
	    c[fields[i]] = i;
	    print x,id,ds,t,au,fields[i], final;
	  }
	}
      }
    } 
  }
  close (fn);
}
