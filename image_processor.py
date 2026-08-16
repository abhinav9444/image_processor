#!/usr/bin/env python3
"""E-Commerce Image Processor."""
from __future__ import annotations
import argparse, json, logging, re, sys, time
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError
SUPPORTED_INPUT_FORMATS={".jpg",".jpeg",".png",".webp",".bmp",".tif",".tiff",".avif"}
SUPPORTED_OUTPUT_FORMATS={"JPEG","PNG","WEBP","AVIF"}
DEFAULT_STANDARD_RESOLUTIONS={"tiny":(100,100),"thumbnail":(150,150),"small":(300,300),"card":(400,400),"medium":(600,600),"detail":(800,800),"large":(1200,1200)}
@dataclass(frozen=True)
class Resolution: name:str; width:int; height:int
@dataclass
class ProcessingStats:
    processed:int=0; failed:int=0; warnings:int=0; original_bytes:int=0; output_bytes:int=0; start_time:float=0.0
    @property
    def saved_bytes(self): return max(0,self.original_bytes-self.output_bytes)
    @property
    def compression_percentage(self): return 0.0 if self.original_bytes==0 else self.saved_bytes/self.original_bytes*100
    @property
    def elapsed_seconds(self): return time.time()-self.start_time
def setup_logging(log_file):
    logger=logging.getLogger("image_processor"); logger.setLevel(logging.INFO); logger.handlers.clear(); formatter=logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console=logging.StreamHandler(sys.stdout); console.setFormatter(formatter); log_file.parent.mkdir(parents=True,exist_ok=True); fh=logging.FileHandler(log_file,encoding="utf-8"); fh.setFormatter(formatter); logger.addHandler(console); logger.addHandler(fh); return logger
def create_default_config(path):
    config={"paths":{"input_dir":"./input","output_dir":"./output","report_file":"./processing_report.json"},"output_format":"WEBP","quality":85,"fit_mode":"contain","background":{"r":255,"g":255,"b":255},"standard_resolutions":{n:list(s) for n,s in DEFAULT_STANDARD_RESOLUTIONS.items()},"enabled_resolutions":["thumbnail","card","detail"],"custom_resolutions":[],"enhancement":{"brightness":1.0,"contrast":1.0,"saturation":1.0,"sharpness":1.0,"noise_reduction":0,"sharpen":0},"quality_check":{"minimum_width":300,"minimum_height":300,"minimum_quality_score":5.0}}
    path.write_text(json.dumps(config,indent=4)+"\n",encoding="utf-8")
def load_config(path):
    if not path.exists(): create_default_config(path); print(f"Created default config: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
def validate_config(config):
    if config.get("output_format","WEBP").upper() not in SUPPORTED_OUTPUT_FORMATS: raise ValueError("Unsupported output format")
    if not 1<=int(config.get("quality",85))<=100: raise ValueError("quality must be between 1 and 100")
    if config.get("fit_mode","contain") not in {"cover","contain","stretch"}: raise ValueError("fit_mode must be cover, contain, or stretch")
def build_resolutions(config,selected_names=None,custom=None):
    standard=config.get("standard_resolutions",{}); names=selected_names or config.get("enabled_resolutions",["thumbnail","card","detail"]); result=[]
    for name in names:
        if name not in standard: raise ValueError(f"Unknown resolution '{name}'. Available: {', '.join(standard)}")
        w,h=map(int,standard[name]); result.append(Resolution(name,w,h))
    if custom: result.append(Resolution(f"{custom[0]}x{custom[1]}",custom[0],custom[1]))
    for item in config.get("custom_resolutions",[]):
        if len(item)==2: result.append(Resolution(f"{int(item[0])}x{int(item[1])}",int(item[0]),int(item[1])))
    return result
def print_resolutions(config):
    print("\nAvailable standard resolutions\n==============================")
    for n,s in config.get("standard_resolutions",{}).items(): print(f"{n:<12} {s[0]} x {s[1]}")
def normalize_filename(filename):
    stem=Path(filename).stem.lower().replace("&","and"); stem=re.sub(r"[^a-z0-9]+","_",stem); return re.sub(r"_+","_",stem).strip("_") or "image"
def normalize_image_mode(image,background):
    if image.mode=="RGBA":
        canvas=Image.new("RGBA",image.size,background+(255,)); canvas.alpha_composite(image); return canvas.convert("RGB")
    return image.convert("RGB")
def enhance_image(image,e):
    for key,cls in [("brightness",ImageEnhance.Brightness),("contrast",ImageEnhance.Contrast),("saturation",ImageEnhance.Color),("sharpness",ImageEnhance.Sharpness)]:
        value=float(e.get(key,1.0))
        if value!=1.0: image=cls(image).enhance(value)
    return image
def resize_image(image,resolution,fit_mode,background):
    size=(resolution.width,resolution.height)
    if fit_mode=="cover": return ImageOps.fit(image,size,method=Image.Resampling.LANCZOS)
    if fit_mode=="stretch": return image.resize(size,Image.Resampling.LANCZOS)
    canvas=Image.new("RGB",size,background); copy=image.copy(); copy.thumbnail(size,Image.Resampling.LANCZOS); canvas.paste(copy,((size[0]-copy.width)//2,(size[1]-copy.height)//2)); return canvas
def estimate_quality(image):
    gray=image.convert("L"); edges=gray.filter(ImageFilter.FIND_EDGES); total=gray.width*gray.height; return 0 if total==0 else sum(i*c for i,c in enumerate(edges.histogram()))/total
def validate_image(image,q):
    warnings=[]
    if image.width<int(q.get("minimum_width",300)): warnings.append(f"Source width {image.width}px is below {q.get('minimum_width',300)}px")
    if image.height<int(q.get("minimum_height",300)): warnings.append(f"Source height {image.height}px is below {q.get('minimum_height',300)}px")
    score=estimate_quality(image)
    if score<float(q.get("minimum_quality_score",5.0)): warnings.append(f"Potentially low-quality/blurry image (score={score:.2f})")
    return warnings
def save_image(image,path,fmt,quality):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fmt=="JPEG": image.convert("RGB").save(path,format="JPEG",quality=quality,optimize=True,progressive=True)
    elif fmt=="WEBP": image.save(path,format="WEBP",quality=quality,method=6)
    elif fmt=="PNG": image.save(path,format="PNG",optimize=True,compress_level=9)
    elif fmt=="AVIF": image.save(path,format="AVIF",quality=quality)
    else: raise ValueError(f"Unsupported output format: {fmt}")
    return path.stat().st_size
def find_images(directory): return sorted(p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_INPUT_FORMATS)
def process_image(input_path,output_dir,resolutions,fmt,quality,fit_mode,background,enhancement,qconfig,dry_run,logger,stats):
    try:
        stats.original_bytes+=input_path.stat().st_size
        with Image.open(input_path) as source:
            image=ImageOps.exif_transpose(source)
            for warning in validate_image(image,qconfig): stats.warnings+=1; logger.warning("%s | %s",input_path.name,warning)
            image=normalize_image_mode(image,background); image=enhance_image(image,enhancement)
            noise=int(enhancement.get("noise_reduction",0))
            if noise>0: image=image.filter(ImageFilter.MedianFilter(size=max(1,min(noise,5))*2+1))
            sharpen=int(enhancement.get("sharpen",0))
            for _ in range(max(0,min(sharpen,5))): image=image.filter(ImageFilter.UnsharpMask(radius=1.0,percent=100,threshold=3))
            base=normalize_filename(input_path.name); ext="jpg" if fmt=="JPEG" else fmt.lower()
            for resolution in resolutions:
                out=output_dir/resolution.name/f"{base}_{resolution.name}.{ext}"
                if dry_run: logger.info("[DRY RUN] Would create: %s",out); continue
                size=save_image(resize_image(image,resolution,fit_mode,background),out,fmt,quality); stats.output_bytes+=size; logger.info("Created %s | %dx%d | %.2f KB",out,resolution.width,resolution.height,size/1024)
            stats.processed+=1
    except (UnidentifiedImageError,OSError,ValueError) as error: stats.failed+=1; logger.error("Failed: %s | %s",input_path,error)
def generate_report(path,stats,resolutions,fmt,quality,fit_mode):
    report={"processing":{"processed":stats.processed,"failed":stats.failed,"warnings":stats.warnings},"configuration":{"format":fmt,"quality":quality,"fit_mode":fit_mode,"resolutions":[{"name":r.name,"width":r.width,"height":r.height} for r in resolutions]},"storage":{"original_mb":round(stats.original_bytes/1024/1024,2),"output_mb":round(stats.output_bytes/1024/1024,2),"saved_mb":round(stats.saved_bytes/1024/1024,2),"compression_percentage":round(stats.compression_percentage,2)},"performance":{"elapsed_seconds":round(stats.elapsed_seconds,2)}}
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(report,indent=4)+"\n",encoding="utf-8")
def build_parser():
    p=argparse.ArgumentParser(description="Batch image processor for e-commerce product assets."); p.add_argument("input",nargs="?",type=Path,help="Input image directory (legacy positional option)"); p.add_argument("-o","--output",type=Path,default=None,help="Output directory (overrides config)"); p.add_argument("--input-dir",type=Path,default=None,help="Input directory (overrides config)"); p.add_argument("--output-dir",type=Path,default=None,help="Output directory (overrides config)"); p.add_argument("--config",type=Path,default=Path("config.json")); p.add_argument("--resolution"); p.add_argument("--resolutions",nargs="+"); p.add_argument("--custom-resolution",nargs=2,type=int,metavar=("WIDTH","HEIGHT")); p.add_argument("--list-resolutions",action="store_true"); p.add_argument("--format",choices=sorted(SUPPORTED_OUTPUT_FORMATS)); p.add_argument("--quality",type=int); p.add_argument("--fit",choices=["cover","contain","stretch"]); p.add_argument("--dry-run",action="store_true"); p.add_argument("--report",type=Path,default=Path("processing_report.json")); return p
def main():
    parser=build_parser(); args=parser.parse_args(); config=load_config(args.config)
    if args.list_resolutions: print_resolutions(config); return 0
    paths=config.get("paths",{}); input_dir=args.input_dir or args.input or Path(paths.get("input_dir","./input")); output_dir=args.output_dir or args.output or Path(paths.get("output_dir","./output"))
    if not input_dir.exists() or not input_dir.is_dir(): parser.error(f"Input directory does not exist or is not a directory: {input_dir}")
    try:
        validate_config(config); fmt=(args.format or config.get("output_format","WEBP")).upper(); quality=args.quality if args.quality is not None else int(config.get("quality",85)); fit=args.fit or config.get("fit_mode","contain")
        if not 1<=quality<=100: raise ValueError("quality must be between 1 and 100")
        selected=args.resolutions if args.resolutions else ([args.resolution] if args.resolution else None); resolutions=build_resolutions(config,selected,tuple(args.custom_resolution) if args.custom_resolution else None)
        if not resolutions: raise ValueError("No resolutions selected.")
    except ValueError as error: parser.error(str(error))
    bg=config.get("background",{}); background=(int(bg.get("r",255)),int(bg.get("g",255)),int(bg.get("b",255))); output_dir.mkdir(parents=True,exist_ok=True); logger=setup_logging(output_dir/"image_processor.log"); images=find_images(input_dir)
    if not images: logger.warning("No supported images found."); return 0
    stats=ProcessingStats(start_time=time.time())
    for image_path in images: process_image(image_path,output_dir,resolutions,fmt,quality,fit,background,config.get("enhancement",{}),config.get("quality_check",{}),args.dry_run,logger,stats)
    report=Path(paths.get("report_file",str(output_dir/"processing_report.json"))) if args.report==Path("processing_report.json") else args.report; generate_report(report,stats,resolutions,fmt,quality,fit)
    logger.info("PROCESSING COMPLETE | processed=%d failed=%d warnings=%d",stats.processed,stats.failed,stats.warnings); return 0
if __name__=="__main__": raise SystemExit(main())
