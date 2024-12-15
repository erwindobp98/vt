import time
import math
import random
from web3 import Web3
import colorama
from colorama import Fore, Style

# Inisialisasi colorama untuk dukungan ANSI warna
colorama.init(autoreset=True)

# Warna ANSI untuk output
RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"

def art():
    width = 50  # Lebar area teks yang ingin dipusatkan
    print(Fore.YELLOW + r"""
================================================
""" + "Airdrop Community".center(width) + """
================================================
""" + "Bot : TAIKO".center(width) + """
""" + "Telegram Channel : @airdropcom9".center(width) + """
""" + "Telegram Group : @airdropcom8".center(width) + """
================================================
""" + Fore.GREEN)

if __name__ == "__main__":
    art()

# Konfigurasi dan inisialisasi variabel
RPC_URL = "https://rpc.taiko.tools"  # Input URL RPC secara manual
PRIVATE_KEY = "isi private key"  # Input Private Key secara manual
CONTRACT_VOTE = '0x4D1E2145082d0AB0fDa4a973dC4887C7295e21aB'  # Alamat kontrak voting
ABI_VOTE = [
    {"stateMutability": "payable", "type": "fallback"},
    {"inputs": [], "name": "vote", "outputs": [], "stateMutability": "payable", "type": "function"}
]  # ABI dari kontrak, termasuk metode "vote"
CHAIN_ID = 0x28c58  # ID chain untuk jaringan Taiko Mainnet
GAS_USAGE = 21116  # Estimasi gas yang digunakan
TOTAL_POINT = int(input("Masukkan total poin yang ingin dicapai default daily max point 73580: "))  # Total poin target dari pengguna

# Setup Web3 dan kontrak
web3 = Web3(Web3.HTTPProvider(RPC_URL))  # Inisialisasi koneksi Web3
contract = web3.eth.contract(address=CONTRACT_VOTE, abi=ABI_VOTE)  # Inisialisasi kontrak voting
account = web3.eth.account.from_key(PRIVATE_KEY)  # Buat objek akun menggunakan private key

# Fungsi untuk inisialisasi voting
def initialize_voting(nonce, gas_increase):
    try:
        encoded_data = contract.functions.vote()._encode_transaction_data()  # Encode data transaksi untuk voting
        estimated_gas = web3.eth.estimate_gas({"to": CONTRACT_VOTE, "data": encoded_data})  # Estimasi gas transaksi
        gas_limit = estimated_gas * 2  # Set batas gas dengan buffer 2x dari estimasi
        max_priority_fee_per_gas = web3.eth.gas_price * (100 + gas_increase) // 100  # Hitung prioritas fee gas
        max_fee_per_gas = Web3.to_wei(0.234, 'gwei')  # Set batas maksimum fee per gas

        tx = {
            "nonce": nonce,  # Nonce transaksi
            "to": CONTRACT_VOTE,  # Alamat kontrak
            "data": encoded_data,  # Data transaksi
            "value": 0,  # Jumlah ETH yang dikirim
            "maxPriorityFeePerGas": max_priority_fee_per_gas,  # Fee prioritas maksimum
            "maxFeePerGas": max_fee_per_gas,  # Fee maksimum
            "gas": gas_limit,  # Batas gas
            "type": 2,  # Tipe transaksi EIP-1559
            "chainId": CHAIN_ID  # ID chain jaringan
        }
        fee = Web3.from_wei(max_priority_fee_per_gas * estimated_gas, 'ether')  # Hitung biaya fee dalam ETH
        return tx, fee  # Mengembalikan transaksi dan fee
    except Exception as e:
        print(f"{RED}Error sending vote: {e}{RESET}")  # Tampilkan pesan error dengan warna merah
        return None, None

# Fungsi untuk memproses total gas
def process_total_gas(total_gas, gas_price):
    avg_gas_per_tnx = Web3.from_wei(gas_price * GAS_USAGE, 'ether')  # Hitung rata-rata gas per transaksi
    avg_gas_per_tnx = float(avg_gas_per_tnx)  # Pastikan menjadi float

    if avg_gas_per_tnx > 0.0000045:  # Batasi jika rata-rata gas terlalu tinggi
        print(f"{YELLOW}Gas price is too high, please wait and try again!{RESET}")
        return None, None, None

    tnx_per_batch = random.randint(15, 20)  # Tentukan ukuran batch secara acak antara 10-15
    gas_fee_increase_percent = round((0.0000045 - avg_gas_per_tnx) / avg_gas_per_tnx * 100)  # Hitung persentase kenaikan fee
    avg_gas_per_tnx *= (gas_fee_increase_percent / 100) + 1  # Update rata-rata gas per transaksi
    
    total_gas = float(total_gas)  # Konversi total gas ke float
    num_tnx = math.ceil(total_gas / avg_gas_per_tnx)  # Hitung total jumlah transaksi yang dibutuhkan
    return num_tnx, tnx_per_batch, gas_fee_increase_percent  # Kembalikan jumlah transaksi, ukuran batch, dan kenaikan fee

# Fungsi utama untuk mengirim transaksi
def send_tnx():
    avg_gas_price = sum([web3.eth.gas_price for _ in range(30)]) // 30  # Hitung harga gas rata-rata dari 30 sampel

    total_gas_in_wei = Web3.to_wei(math.ceil(TOTAL_POINT / 2.1 * 10), 'gwei')  # Hitung total gas dalam wei
    total_gas = Web3.from_wei(total_gas_in_wei, 'ether')  # Konversi total gas ke ether

    print(f"{BLUE}\nTotal Point: {TOTAL_POINT}{RESET}")
    print(f"{BLUE}Total gas: {total_gas}{RESET}")

    num_tnx, tnx_per_batch, gas_fee_increase_percent = process_total_gas(total_gas, avg_gas_price)  # Proses estimasi total gas
    
    if num_tnx is None or tnx_per_batch is None:  # Jika gas terlalu tinggi, batalkan
        return

    nonce = web3.eth.get_transaction_count(account.address)  # Dapatkan nonce akun

    tx_count = 0  # Hitungan transaksi yang sukses
    failed_tx_count = 0  # Hitungan transaksi yang gagal

    # Start measuring time
    start_time = time.time()  # Record the start time

    while tx_count < num_tnx:  # Lakukan pengiriman sampai mencapai jumlah transaksi yang diperlukan
        batch_size = min(tnx_per_batch, num_tnx - tx_count)  # Tentukan ukuran batch berdasarkan sisa transaksi
        print(f"{GREEN}\nSending {batch_size} transactions with NONCE start {nonce}...{RESET}")
        tx, fee = initialize_voting(nonce, gas_fee_increase_percent)  # Inisialisasi transaksi

        if tx is None:  # Jika inisialisasi gagal, batalkan
            print(f"{RED}Transaction initialization failed{RESET}")
            break

        for _ in range(batch_size):  # Kirim batch transaksi
            try:
                signed_tx = account.sign_transaction(tx)  # Tanda tangani transaksi
                web3.eth.send_raw_transaction(signed_tx.raw_transaction)  # Kirim transaksi
                print(f"{GREEN}Fee: {fee} ETH{RESET}")
                nonce += 1  # Tingkatkan nonce
                tx["nonce"] = nonce  # Update nonce dalam transaksi berikutnya
                time.sleep(10)  # Tunggu sebentar sebelum transaksi berikutnya
            except Exception as e:
                print(f"{RED}Sending Tnx Error: {e}{RESET}")  # Jika ada kesalahan, tampilkan pesan error
                failed_tx_count += 1  # Hitung transaksi yang gagal
                continue

        tx_count += batch_size - failed_tx_count  # Update hitungan transaksi yang berhasil
        if failed_tx_count > 0:  # Jika ada transaksi gagal, tingkatkan fee
            gas_fee_increase_percent += 2
            print(f"{YELLOW}(+) GAS_FEE_INCREASE_PERCENT {gas_fee_increase_percent}%{RESET}")
            failed_tx_count = 0  # Reset hitungan transaksi yang gagal

        # Calculate and print elapsed time
        elapsed_time = time.time() - start_time  # Get the elapsed time in seconds
        print(f"{YELLOW}Elapsed time: {elapsed_time:.2f} seconds{RESET}")

        # Print remaining wait time before the next batch of transactions
        remaining_time = 10  # Set the wait time to an integer value (e.g., 10 seconds)
        print(f"{YELLOW}Waiting for {remaining_time} seconds before sending next batch...{RESET}")
        time.sleep(remaining_time)  # Tunggu sebentar sebelum batch transaksi berikutnya

if __name__ == "__main__":
    try:
        send_tnx()  # Panggil fungsi utama untuk memulai proses transaksi
    except KeyboardInterrupt:
        print(Fore.RED + "\nInterrupted by user." + Style.RESET_ALL)
    finally:
        print(Fore.YELLOW + "Thank you tod!" + Style.RESET_ALL)
