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
}
{
  x = $1;
  fn = $2;
  gsub(/_/,"/", fn);
  fn = "abs/"fn".abs"
  where = 0;
  t = "";
  au = "";
  delete c;
  delete fields;
  while ((getline line < fn) > 0) {
    len=split(line, fields);
    if (line ~ /^arXiv:/) {
      id=substr(line,7);
    }
    if (line ~ /^Date:/) {
      ds=sprintf("%s-%s-%02d %s",fields[5],a[fields[4]],fields[3],fields[6])
    }
    if (line ~ /^Title:/) {
      t=substr(line, index(line,fields[2]));
      where=1;
    }
    if (line ~ /^Authors:/) {
      au=substr(line, index(line,fields[2]));
      where=2;
    }
    if (line ~ /^  /) {
      if (where==1)
	t=t""line;
      else if (where==2) 
	au=au""line;
    }
    if (line ~ /^\\/) {
      where=0;
    }
    if (line ~ /^Categories:/) {
      where = 0;
      # loop over all categories
      for (i=2; i<=len; i++) {
	c[i] = fields[i];
      }
    } 
  }
  close (fn);
  for (i in c)
    print x,id,ds,t,au,c[i];
}
