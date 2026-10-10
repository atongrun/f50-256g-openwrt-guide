import importlib.util,pathlib,struct,zlib,unittest
spec=importlib.util.spec_from_file_location('gpt',pathlib.Path(__file__).parents[1]/'scripts/check-gpt.py')
gpt=importlib.util.module_from_spec(spec);spec.loader.exec_module(gpt)

def fixture(overlap=False,outside=False):
    sector=512;n=10000;array=bytearray(128*128)
    for i,(start,end) in enumerate([(2048,4095),(4000 if overlap else 4096,10001 if outside else 9000)]):
        off=i*128;array[off:off+16]=b'\x01'*16;array[off+16:off+32]=bytes([i+2])*16
        struct.pack_into('<QQ',array,off+32,start,end)
        name=('boot_a' if i==0 else 'userdata').encode('utf-16-le');array[off+56:off+56+len(name)]=name
    def head(cur,other,arr):
        raw=bytearray(sector);raw[:8]=b'EFI PART';struct.pack_into('<IIII',raw,8,0x10000,92,0,0)
        struct.pack_into('<QQQQ',raw,24,cur,other,34,n-34);raw[56:72]=b'\x03'*16
        struct.pack_into('<QIII',raw,72,arr,128,128,zlib.crc32(array)&0xffffffff)
        struct.pack_into('<I',raw,16,zlib.crc32(raw[:92])&0xffffffff);return raw
    return bytes(sector)+head(1,n-1,2)+array,array+head(n-1,1,n-33),n*sector

class GPTTests(unittest.TestCase):
    def test_valid(self):
        a,b,size=fixture();r=gpt.validate(a,b,size);self.assertEqual(r['partition_count'],2)
    def test_crc(self):
        a,b,size=fixture();a=bytearray(a);a[512+16]^=1
        with self.assertRaisesRegex(ValueError,'CRC'):gpt.validate(a,b,size)
    def test_overlap(self):
        with self.assertRaisesRegex(ValueError,'Overlapping'):gpt.validate(*fixture(overlap=True))
    def test_outside(self):
        with self.assertRaisesRegex(ValueError,'outside'):gpt.validate(*fixture(outside=True))
    def test_wrong_capacity(self):
        a,b,size=fixture()
        with self.assertRaises(ValueError):gpt.validate(a,b,size+512)
    def test_truncated(self):
        a,b,size=fixture()
        with self.assertRaises(ValueError):gpt.validate(a,b[512:],size)
if __name__=='__main__':unittest.main()
