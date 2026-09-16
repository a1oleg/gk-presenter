"""Resolve an exact Google Slides page URL from a sheet to a local PNG.

Uses the existing Google connector credentials; no keys or temporary signed URLs
are copied into the presenter output. Run with google-sheets-mcp's Python.
"""
import argparse,hashlib,json,re,sys,urllib.parse,urllib.request,struct
from pathlib import Path
from google.auth.transport.requests import AuthorizedSession

def parse_slide_url(url):
 parsed=urllib.parse.urlparse(url.strip().strip('"'))
 if parsed.scheme!='https' or parsed.hostname!='docs.google.com':raise ValueError('Expected an HTTPS Google Slides URL')
 match=re.fullmatch(r'/presentation/d/([A-Za-z0-9_-]+)/(?:edit|preview|present)/?',parsed.path)
 if not match:raise ValueError('Unsupported presentation URL')
 query=urllib.parse.parse_qs(parsed.query);fragment=urllib.parse.parse_qs(parsed.fragment)
 target=(fragment.get('slide') or query.get('slide') or [''])[0]
 if not re.fullmatch(r'id\.[A-Za-z0-9_-]+',target):raise ValueError('Link must identify one slide: #slide=id.…')
 return match[1],target[3:]

def fetch_slide(url,out):
 presentation,page=parse_slide_url(url)
 sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'google-sheets-mcp'))
 from server import build_credentials
 session=AuthorizedSession(build_credentials())
 response=session.get(f'https://slides.googleapis.com/v1/presentations/{presentation}/pages/{page}/thumbnail',params={'thumbnailProperties.mimeType':'PNG','thumbnailProperties.thumbnailSize':'LARGE'},timeout=60)
 method='Google Slides pages.getThumbnail LARGE'
 if not response.ok:
  error=response.json().get('error',{})
  if response.status_code!=403 or 'disabled' not in error.get('message','').lower():
   raise RuntimeError(f'Google Slides HTTP {response.status_code}: {error.get("message","Access unavailable")}')
  # Public web export is an independent read path; never change document permissions.
  image_url=f'https://docs.google.com/presentation/d/{presentation}/export/png?'+urllib.parse.urlencode({'id':presentation,'pageid':page})
  method='Public Google Slides PNG export (Slides API disabled)'
 else:
  data=response.json();image_url=data['contentUrl'];download=urllib.parse.urlparse(image_url)
  if download.scheme!='https' or not (download.hostname or '').endswith('.googleusercontent.com'):raise RuntimeError('Unexpected thumbnail host')
 with urllib.request.urlopen(image_url,timeout=60) as r:png=r.read(20_000_001)
 if len(png)>20_000_000 or png[:8]!=b'\x89PNG\r\n\x1a\n':raise RuntimeError('Invalid thumbnail image')
 width,height=struct.unpack('>II',png[16:24])
 out.mkdir(parents=True,exist_ok=True)
 image=out/'google-slide.png'
 if image.exists():raise RuntimeError('Slide already captured; choose a new output directory')
 image.write_bytes(png)
 report={'sourceUrl':url,'presentationId':presentation,'pageObjectId':page,'image':str(image.resolve()),'width':width,'height':height,'sha256':hashlib.sha256(png).hexdigest(),'method':method,'animationIncluded':False}
 (out/'google-slide.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('output',type=Path);a=p.parse_args()
 print(json.dumps(fetch_slide(a.url,a.output),ensure_ascii=False))
