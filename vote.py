import sys
import requests
import datetime
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

def animated_print(text, delay=0.02, color=Fore.WHITE):
    """
    Fungsi untuk mencetak teks dengan efek animasi karakter per karakter.
    :param text: Teks yang akan dicetak
    :param delay: Waktu jeda antar karakter (dalam detik)
    :param color: Warna teks (gunakan dari colorama.Fore)
    """
    for char in text:
        print(color + char, end="", flush=True)
        time.sleep(delay)
    print(RESET)  # Reset warna di akhir

# Konfigurasi dan inisialisasi variabel
my_address = "0x22F3xxxxxxxxxx" # Input Wallet Address secara manual
RPC_URL = "https://taiko-rpc.publicnode.com"  # Input URL RPC secara manual
PRIVATE_KEY = "0x686xxxxxxxxxxx"  # Input Private Key secara manual
CONTRACT_VOTE = '0x4D1E2145082d0AB0fDa4a973dC4887C7295e21aB'  # Alamat kontrak voting
ABI_VOTE = [
    {"stateMutability": "payable", "type": "fallback"},
    {"inputs": [], "name": "vote", "outputs": [], "stateMutability": "payable", "type": "function"}
]  # ABI dari kontrak, termasuk metode "vote"
CHAIN_ID = 0x28c58  # ID chain untuk jaringan Taiko Mainnet
GAS_USAGE = 21116  # Estimasi gas yang digunakan
TOTAL_POINT = int(input("Masukkan total poin yang ingin dicapai: "))  # Total poin target dari pengguna

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

        # Rentang min dan max untuk gas fee dalam Gwei
        min_gas_price_gwei = 0.234  # Minimum gas price dalam Gwei
        max_gas_price_gwei = 0.24  # Maksimum gas price dalam Gwei

        # Hitung maxPriorityFeePerGas dan maxFeePerGas berdasarkan rentang
        max_priority_fee_per_gas = Web3.to_wei(random.uniform(min_gas_price_gwei, max_gas_price_gwei), 'gwei')
        max_fee_per_gas = Web3.to_wei(max_gas_price_gwei, 'gwei')  # Batas maksimum fee per gas

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

    if avg_gas_per_tnx > 0.0000047:  # Batasi jika rata-rata gas terlalu tinggi
        print(f"{YELLOW}Gas price is too high, please wait and try again!{RESET}")
        return None, None, None

    tnx_per_batch = random.randint(5, 10)  # Tentukan ukuran batch secara acak antara 5-10
    gas_fee_increase_percent = round((0.0000047 - avg_gas_per_tnx) / avg_gas_per_tnx * 100)  # Hitung persentase kenaikan fee
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
                time.sleep(6)  # Tunggu sebentar sebelum transaksi berikutnya
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
        remaining_time = 6  # Set the wait time to an integer value (e.g., 6 seconds)
        print(f"{YELLOW}Waiting for {remaining_time} seconds before sending next batch...{RESET}")
        time.sleep(remaining_time)  # Tunggu sebentar sebelum batch transaksi berikutnya

def calculate_gas_fee(gas_used, gas_price_gwei):
    gas_price_wei = gas_price_gwei * 1e9
    gas_fee_wei = gas_used * gas_price_wei
    return gas_fee_wei / 1e18

def get_eth_price():
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd'
        response = requests.get(url)
        data = response.json()
        
        if 'ethereum' not in data or 'usd' not in data['ethereum']:
            print(Fore.RED + 'Gagal mendapatkan harga ETH.')
            return None
        
        return data['ethereum']['usd']
    except requests.RequestException as e:
        print(Fore.RED + f'Error fetching ETH price: {e}')
        return None

def get_transaction_data_from_taiko(my_address):
    try:
        now = int(time.time())
        start_of_today = int(datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        start_of_period = int(datetime.datetime(2024, 9, 16, tzinfo=datetime.timezone.utc).timestamp())
        
        url = f'https://api.taikoscan.io/api?module=account&action=txlist&address={my_address}'
        response = requests.get(url)
        
        if response.status_code != 200:
            print(Fore.RED + f"Failed to fetch transaction data: {response.status_code}")
            return
        
        data = response.json()
        
        if 'result' not in data:
            print(Fore.YELLOW + 'Tidak ada data transaksi ditemukan.')
            return

        total_gas_fee_today = 0
        tx_count_today = 0
        total_gas_fee_from_sep16 = 0
        tx_count_from_sep16 = 0
        
        for tx in data['result']:
            tx_timestamp = int(tx['timeStamp'])
            gas_used = int(tx['gasUsed'])
            gas_price_gwei = int(tx['gasPrice'])

            gas_fee = calculate_gas_fee(gas_used, gas_price_gwei)
            
            if tx_timestamp >= start_of_today:
                total_gas_fee_today += gas_fee
                tx_count_today += 1

            if tx_timestamp >= start_of_period:
                total_gas_fee_from_sep16 += gas_fee
                tx_count_from_sep16 += 1
        
        eth_to_usd_rate = get_eth_price()
        
        if not eth_to_usd_rate:
            print(Fore.RED + 'Gagal mendapatkan harga ETH, perhitungan tidak dapat dilanjutkan.')
            return
        
        adjusted_gas_fee_eth_today = total_gas_fee_today / 1e9
        total_gas_fee_usd_today = adjusted_gas_fee_eth_today * eth_to_usd_rate

        adjusted_gas_fee_eth_from_sep16 = total_gas_fee_from_sep16 / 1e9
        total_gas_fee_usd_from_sep16 = adjusted_gas_fee_eth_from_sep16 * eth_to_usd_rate

        return {
            'total_gas_fee_today': total_gas_fee_today,
            'tx_count_today': tx_count_today,
            'total_gas_fee_from_sep16': total_gas_fee_from_sep16,
            'tx_count_from_sep16': tx_count_from_sep16,
            'adjusted_gas_fee_eth_today': adjusted_gas_fee_eth_today,
            'total_gas_fee_usd_today': total_gas_fee_usd_today,
            'adjusted_gas_fee_eth_from_sep16': adjusted_gas_fee_eth_from_sep16,
            'total_gas_fee_usd_from_sep16': total_gas_fee_usd_from_sep16
        }

    except requests.RequestException as e:
        print(Fore.RED + f'Error fetching transaction data: {e}')
        return None

def get_final_data(my_address):
    try:
        final_url = f'https://trailblazer.mainnet.taiko.xyz/user/final?address={my_address}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; TaikoRankChecker/1.0)'
        }
        response = requests.get(final_url, headers=headers)

        if response.status_code == 403:
            print(Fore.RED + "Gagal mengambil data final: Akses ditolak (403). Pastikan Anda memiliki izin akses.")
            return None

        if response.status_code != 200:
            print(Fore.RED + f"Gagal mengambil data final: {response.status_code}")
            return None

        data = response.json()
        return {
            "score": data.get('score', 'N/A'),
            "multiplier": data.get('multiplier', 'N/A'),
            "total": data.get('total', 'N/A')
        }
    except requests.RequestException as e:
        print(Fore.RED + f'Error fetching final data: {e}')
        return None

def get_rank_data(my_address):
    try:
        rank_url = f'https://trailblazer.mainnet.taiko.xyz/s2/user/rank?address={my_address}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; TaikoRankChecker/1.0)'
        }
        response = requests.get(rank_url, headers=headers)
        if response.status_code != 200:
            print(Fore.RED + f"Failed to fetch rank data: {response.status_code}")
            return None

        return response.json()
    except requests.RequestException as e:
        print(Fore.RED + f'Error fetching rank data: {e}')
        return None

def display_taiko_data(my_address):
    transaction_data = get_transaction_data_from_taiko(my_address)
    final_data = get_final_data(my_address)
    rank_data = get_rank_data(my_address)

    if transaction_data:
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.01)
        animated_print("                       Taiko Transaction Data S2             ", color=Fore.GREEN, delay=0.01)
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.01)
        if 'adjusted_gas_fee_eth_today' in transaction_data:
            animated_print(f"Gas Fee ETH (Hari Ini)       : {transaction_data['adjusted_gas_fee_eth_today']:.10f} ETH", color=Fore.YELLOW, delay=0.01)
        
        if 'total_gas_fee_usd_today' in transaction_data:
            animated_print(f"Gas Fee USD (Hari Ini)       : ${transaction_data['total_gas_fee_usd_today']:.2f}", color=Fore.YELLOW, delay=0.01)
        
        if 'tx_count_today' in transaction_data:
            animated_print(f"Jumlah Tx Hari Ini           : {transaction_data['tx_count_today']} transaksi", color=Fore.GREEN, delay=0.01)
        
        if 'adjusted_gas_fee_eth_from_sep16' in transaction_data:
            animated_print(f"Total Gas Fee ETH TAIKO S2   : {transaction_data['adjusted_gas_fee_eth_from_sep16']:.10f} ETH", color=Fore.BLUE, delay=0.01)
        
        if 'total_gas_fee_usd_from_sep16' in transaction_data:
            animated_print(f"Total Gas Fee USD TAIKO S2   : ${transaction_data['total_gas_fee_usd_from_sep16']:.2f}", color=Fore.BLUE, delay=0.01)
        
        if 'tx_count_from_sep16' in transaction_data:
            animated_print(f"Jumlah Tx TAIKO S2           : {transaction_data['tx_count_from_sep16']} transaksi", color=Fore.GREEN, delay=0.01)

    if rank_data:
        rank = rank_data.get('rank', 'N/A')
        score = rank_data.get('score', 'N/A')
        multiplier = rank_data.get('multiplier', 'N/A')
        total_score = rank_data.get('totalScore', 'N/A')
        total = rank_data.get('total', 'N/A')
        blacklisted = rank_data.get('blacklisted', 'N/A')
        breakdown = rank_data.get('breakdown', 'N/A')

        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.01)
        animated_print("                       Taiko Rank Data S2           ", color=Fore.GREEN, delay=0.02)
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.01)
        animated_print(f"Rank                         : {rank}", color=Fore.YELLOW, delay=0.01)
        animated_print(f"Score                        : {score}", color=Fore.YELLOW, delay=0.01)
        animated_print(f"Multiplier                   : {multiplier}", color=Fore.CYAN, delay=0.01)
        animated_print(f"Total Score                  : {total_score}", color=Fore.CYAN, delay=0.01)
        animated_print(f"Total                        : {total}", color=Fore.BLUE, delay=0.01)
        animated_print(f"Blacklisted                  : {blacklisted}", color=Fore.RED, delay=0.01)
        animated_print(f"Breakdown                    : {breakdown}", color=Fore.MAGENTA, delay=0.01)

    if final_data:
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.01)
        animated_print("                       Taiko Final Data S1           ", color=Fore.GREEN, delay=0.01)
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.01)
        animated_print(f"Score                        : {final_data['score']}", color=Fore.YELLOW, delay=0.01)
        animated_print(f"Multiplier                   : {final_data['multiplier']}", color=Fore.CYAN, delay=0.01)
        animated_print(f"Total                        : {final_data['total']}", color=Fore.BLUE, delay=0.01)
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.01)
        animated_print("                       Terima kasih tod!              ", color=Fore.YELLOW, delay=0.01)
        animated_print("=================================================================", color=Fore.MAGENTA, delay=0.01)

if __name__ == "__main__":
    try:
        send_tnx()  # Panggil fungsi utama untuk memulai proses transaksi
    except KeyboardInterrupt:
        print(Fore.RED + "\nInterrupted by user." + Style.RESET_ALL)
    finally:
        display_taiko_data(my_address)
