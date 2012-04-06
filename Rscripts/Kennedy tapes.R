source = "http://whitehousetapes.net/transcript/kennedy/dictabelt-412"

JohnsonSources = scan(url("http://whitehousetapes.net/transcript/johnson"),what='raw',sep="\n")
JohnsonSources = JohnsonSources[grep('<a href="johnson/wh',JohnsonSources)]

sources = gsub(".*href=\"","",JohnsonSources)
sources = gsub("\".*","",sources)
lapply(sources,function(source) {
  myfile = download(
  paste(
    "http://whitehousetapes.net/transcript/",
    source,sep=""))
  write.table(myfile,file=paste("~/tv/Johnson Tapes/",gsub(".*/","",source),".srt",sep=""))
})

KennedySources = scan(url("http://whitehousetapes.net/transcript/kennedy/list"),what="raw",sep="\n")
KennedySources = KennedySources[grep('<a href="dictabelt-',KennedySources)]
sources = gsub(".*href=\"","",KennedySources)
sources = gsub("\".*","",sources)
lapply(sources,function(source) {
  myfile = download(
  paste(
    "http://whitehousetapes.net/transcript/Kennedy/",
    source,sep=""))
  write.table(myfile,file=paste("~/tv/Kennedy Tapes/",gsub(".*/","",source),".srt",sep=""))
})
                      
download = function(source) {
  file = scan(url(source),what='raw',sep="\n")
  file = file[grepl("^\\<p",file,perl=T) | grepl('class="sp"',file,perl=T)]
  file = gsub(".*</strong>","",file)
  file = gsub("</p>","",file)
  file = gsub("</div>","",file)

  file = gsub("&rsquo;","'",file)
  file = gsub("&mdash;","--",file)
  file = gsub("&nbsp;","--",file)
  
  
  file = gsub("<[^<>]+>","",file)
  #don't believe brackets, but leave an ellipsis in so bigrams don't span them.
  file = gsub("\\[[^\\[\\]]+\\]","...",file,perl=T)
  file = file[!grepl("digital collections",file)]
}
