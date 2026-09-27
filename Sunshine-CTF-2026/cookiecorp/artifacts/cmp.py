import re,json
vals=["a b","a<b>",'a"b',"a'b","a\\b","a/b","a;b","a=b","a&b","</script>","a\tb","a$b","a`b","a{b}","a%b","a+b","a(b)","a[b]","a,b","a:b","a|b","a\nb","a\x00b","a\u00e9b","a..b","a~b","a!b","a@b","a#b","a^b","a*b","a-b","a_b","a?b"]
html=open("probe_review.html").read()
m=re.search(r"window\.__recipe = (.*);",html)
d=json.loads(m.group(1))
for o,ing in zip(vals,d["ingredients"]):
    status = "SAME" if ing["value"]==o else "CHANGED"
    print(f"{status:8} {o!r} -> {ing['value']!r}")
