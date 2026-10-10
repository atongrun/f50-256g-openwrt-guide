"""Validate offline primary/secondary GPT windows. Never writes a device or image.

Primary window starts at LBA 0; secondary window ends at the last disk LBA.
Use exact binary dumps, not PowerShell text redirects. This tool checks GPT only;
it cannot prove filesystem size, emptiness, compatibility or safe write permission.
"""
import argparse, json, pathlib, struct, zlib

def validate(primary, secondary, disk_bytes, sector=512):
    if sector not in (512,4096) or disk_bytes <= 0 or disk_bytes % sector:
        raise ValueError('Invalid disk size / logical sector size')
    sectors=disk_bytes//sector
    if len(primary)%sector or len(secondary)%sector or min(len(primary),len(secondary))<sector*2:
        raise ValueError('Invalid capture window length')
    if len(primary)>disk_bytes or len(secondary)>disk_bytes:
        raise ValueError('Capture exceeds disk')
    def header(blob,base,lba):
        off=(lba-base)*sector
        if off<0 or off+sector>len(blob):raise ValueError('Header not captured')
        raw=blob[off:off+sector]
        if raw[:8]!=b'EFI PART':raise ValueError('Missing GPT signature')
        rev,size,crc,res=struct.unpack_from('<IIII',raw,8)
        if rev!=0x10000 or not 92<=size<=sector or res!=0:raise ValueError('Unsupported/malformed GPT header')
        tmp=bytearray(raw[:size]);tmp[16:20]=b'\0'*4
        if zlib.crc32(tmp)&0xffffffff!=crc:raise ValueError('Header CRC mismatch')
        cur,other,first,last=struct.unpack_from('<QQQQ',raw,24)
        entries,count,width,arraycrc=struct.unpack_from('<QIII',raw,72)
        if cur!=lba or other>=sectors or not 2<=first<=last<sectors-1:
            raise ValueError('Invalid GPT boundaries')
        if not 0<count<=16384 or width<128 or width%8 or count*width>16*1024*1024:
            raise ValueError('Invalid entry geometry')
        start=(entries-base)*sector;end=start+count*width
        if start<0 or end>len(blob):raise ValueError('Entry array is not fully captured')
        array=blob[start:end]
        if zlib.crc32(array)&0xffffffff!=arraycrc:raise ValueError('Entry array CRC mismatch')
        array_end=entries+(len(array)+sector-1)//sector-1
        if not (array_end<first or entries>last):raise ValueError('GPT array overlaps usable area')
        return dict(cur=cur,other=other,first=first,last=last,guid=raw[56:72],array=array,width=width,count=count,entries=entries,array_end=array_end)
    a=header(primary,0,1);b=header(secondary,sectors-len(secondary)//sector,sectors-1)
    if a['other']!=b['cur'] or b['other']!=a['cur']:raise ValueError('GPT copies do not point to each other')
    for key in ('first','last','guid','array','count','width'):
        if a[key]!=b[key]:raise ValueError('Primary/secondary GPT disagreement: '+key)
    if a['entries']<2 or a['array_end']>=a['first'] or b['entries']<=a['last'] or b['array_end']>=sectors-1:
        raise ValueError('GPT metadata layout overlaps disk data/header')
    parts=[]
    for i in range(a['count']):
        row=a['array'][i*a['width']:(i+1)*a['width']]
        if row[:16]==b'\0'*16:continue
        start,end=struct.unpack_from('<QQ',row,32)
        if not a['first']<=start<=end<=a['last']:raise ValueError('Partition outside usable range')
        name=row[56:128].decode('utf-16-le').split('\0',1)[0]
        parts.append(dict(name=name,start_lba=start,end_lba_inclusive=end,bytes=(end-start+1)*sector))
    parts.sort(key=lambda p:p['start_lba'])
    if not parts:raise ValueError('No partitions')
    for left,right in zip(parts,parts[1:]):
        if left['end_lba_inclusive']>=right['start_lba']:raise ValueError('Overlapping partitions')
    tail=a['last']-parts[-1]['end_lba_inclusive']
    # No GUIDs, identifiers, write offsets or flashing command are emitted.
    return {'valid_gpt':True,'disk_bytes':disk_bytes,'sector_size':sector,'partition_count':len(parts),'tail_unallocated_bytes':tail*sector,'partitions':parts,'warning':'GPT only. Filesystem size and region emptiness have NOT been verified. No writes permitted by this output.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--primary',type=pathlib.Path,required=True);p.add_argument('--secondary',type=pathlib.Path,required=True)
    p.add_argument('--disk-bytes',type=int,required=True);p.add_argument('--sector-size',type=int,default=512)
    args=p.parse_args()
    try:print(json.dumps(validate(args.primary.read_bytes(),args.secondary.read_bytes(),args.disk_bytes,args.sector_size),ensure_ascii=False,indent=2))
    except (ValueError,OSError,UnicodeError) as e:p.exit(2,'STOP: '+str(e)+'\n')
