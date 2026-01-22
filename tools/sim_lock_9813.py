import hashlib
from Crypto.Cipher import AES
import binascii

def pad_imei(imei):
    """将IMEI补足到16位，不足部分用F填充"""
    padded = imei.ljust(16, 'F')
    return padded[:16]

def iso9797_m2_padding(data):
    """ISO/IEC 9797-1 Padding Method 2 (ISO/IEC 7816-4 compliant)"""
    # 添加一个1位的比特'1'（即0x80）
    padded_data = data + b'\x80'
    
    # 添加尽可能多的0位，直到数据长度为块大小的倍数
    while len(padded_data) % 16 != 0:
        padded_data += b'\x00'
        
    return padded_data

def sim_lock_algorithm(iccid, imei, ar, key, dr):
    """
    实现SIM锁算法
    
    Args:
        iccid: ICCID号码
        imei: IMEI号码
        ar: 应用随机数
        key: 认证根密钥
        dr: 终端随机数
    
    Returns:
        加密后的密文
    """
    
    # 步骤2: 拼接IMEI和ICCID
    padded_imei = pad_imei(imei)
    concatenated = padded_imei + iccid
    print(f"IMEI|ICCID: {concatenated}")
    
    # 步骤3: 转换为16进制字节串V
    h_bytes = bytes.fromhex(concatenated)
    
    # 步骤4: 对H进行SHA1计算
    sha1_hash = hashlib.sha1(h_bytes).hexdigest().upper()
    print(f"SHA1结果: {sha1_hash}")
    
    # 步骤5: 取右16字节数据V
    v_hex = sha1_hash[-32:]  # 16字节=32个十六进制字符
    print(f"H: {v_hex}")
    
    # 步骤6: 使用KEY对V进行AES-ECB-128加密得到设备密钥K
    key_bytes = bytes.fromhex(key)
    v_bytes = bytes.fromhex(v_hex)
    
    cipher_ecb = AES.new(key_bytes, AES.MODE_ECB)
    k_bytes = cipher_ecb.encrypt(v_bytes)
    k_hex = k_bytes.hex().upper()
    print(f"设备密钥K: {k_hex}")
    
    # 步骤7: 拼接待加密数据S
    s_concatenated = dr + ar + padded_imei + iccid
    print(f"DR|AR|IMEI|ICCID: {s_concatenated}")
    
    # 将S转换为字节串
    s_bytes = bytes.fromhex(s_concatenated)
    
    # 步骤8: 使用设备密钥K对S进行AES-CBC-128加密，IV=全0，填充方式为ISO9797_M2
    # 应用ISO9797_M2填充
    s_bytes_padded = iso9797_m2_padding(s_bytes)
    print(f"待加密数据      : {s_bytes_padded.hex().upper()}")
    
    iv = bytes(16)  # 全0的IV
    cipher_cbc = AES.new(k_bytes, AES.MODE_CBC, iv)
    encrypted_bytes = cipher_cbc.encrypt(s_bytes_padded)
    ciphertext = encrypted_bytes.hex().upper()
    
    return ciphertext

def get_user_input():
    """获取用户输入"""
    print("请输入以下参数：")
    iccid = input("ICCID (默认: FFFFFFFFFFFFFFFFFFFF): ").strip() or "FFFFFFFFFFFFFFFFFFFF"
    imei = input("IMEI (默认: 112233445566778F): ").strip() or "112233445566778F"
    ar = input("应用随机数AR (默认: 4D4E0EF94AC9E7E8): ").strip() or "4D4E0EF94AC9E7E8"
    key = input("认证根密钥KEY (默认: 0997389F09EE1A2C07BE35C670F5CD74): ").strip() or "0997389F09EE1A2C07BE35C670F5CD74"
    dr = input("终端随机数DR (默认: E9FD3589C39B7C75): ").strip() or "E9FD3589C39B7C75"
    
    return iccid, imei, ar, key, dr

def main():
    print("SIM锁算法实现")
    print("=" * 50)
    rrk = '404142434445464748494a4b4c4d4e4f'
    fsyz = '0003FFFFFFFFFFFFFFFFFFFFFFFF0003'
    fsyz_bytes = bytes.fromhex(fsyz)
    rrk_bytes = bytes.fromhex(rrk)
    cipher_ecb = AES.new(rrk_bytes, AES.MODE_ECB)
    k_bytes = cipher_ecb.encrypt(fsyz_bytes)
    rk = k_bytes.hex().upper()
    print(f"厂商密钥: {rk}")
    
    # 询问用户是否使用默认值
    use_default = input("是否使用默认示例值？(y/n, 默认:y): ").strip().lower()
    
    if use_default == 'n' or use_default == 'no':
        iccid, imei, ar, key, dr = get_user_input()
    else:
        # 使用默认示例值
        iccid = "FFFFFFFFFFFFFFFFFFFF"
        imei = "112233445566778F"
        ar = "4D4E0EF94AC9E7E8"
        key = "0997389F09EE1A2C07BE35C670F5CD74"
        dr = "E9FD3589C39B7C75"
    
    print("=" * 50)
    print(f"ICCID: {iccid}")
    print(f"IMEI: {imei}")
    print(f"AR: {ar}")
    print(f"KEY: {key}")
    print(f"DR: {dr}")
    print("=" * 50)
    
    # 执行算法
    result = sim_lock_algorithm(iccid, imei, ar, key, dr)
    
    # 输出结果
    print("=" * 50)
    print(f"设备密文: {result}")

if __name__ == "__main__":
    main()