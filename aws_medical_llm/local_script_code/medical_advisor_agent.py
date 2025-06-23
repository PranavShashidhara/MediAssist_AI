from llama_cpp import Llama
import os
import time
import requests
from pathlib import Path
from typing import Optional
from tqdm import tqdm

def download_model(download_dir: str = "./models") -> str:
    """
    Download BioGPT Q5_K_M GGUF model from Hugging Face
    
    Args:
        download_dir: Directory to save the model
    
    Returns:
        Path to the downloaded model file
    """
    model_name = "biogpt-baseline.Q5_K_M.gguf"
    model_size = "~800MB (higher quality)"
    
    # Create download directory
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    model_path = os.path.join(download_dir, model_name)
    
    # Check if model already exists
    if os.path.exists(model_path):
        print(f"✅ Model already exists: {model_path}")
        return model_path
    
    # Download URL
    base_url = "https://huggingface.co/RichardErkhov/akhilanilkumar_-_biogpt-baseline-gguf/resolve/main"
    download_url = f"{base_url}/{model_name}"
    
    print(f"📥 Downloading {model_name}...")
    print(f"💾 Size: {model_size}")
    print(f"🔗 URL: {download_url}")
    
    try:
        # Start download with progress bar
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(model_path, 'wb') as file, tqdm(
            desc=model_name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    pbar.update(len(chunk))
        
        print(f"✅ Download completed: {model_path}")
        return model_path
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Download failed: {e}")
        # Clean up partial download
        if os.path.exists(model_path):
            os.remove(model_path)
        raise

class BioGPTChat:
    def __init__(self, model_path: str, n_ctx: int = 2048, n_threads: Optional[int] = None):
        """
        Initialize BioGPT model with GGUF format for optimized CPU inference
        
        Args:
            model_path: Path to the downloaded GGUF model file
            n_ctx: Context window size (default 2048)
            n_threads: Number of CPU threads (auto-detect if None)
        """
        # Auto-detect CPU threads if not specified
        if n_threads is None:
            n_threads = min(8, os.cpu_count())  # Cap at 8 for optimal performance
        
        print(f"Loading model with {n_threads} threads...")
        start_time = time.time()
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=0,  # CPU only
            verbose=False,
            use_mmap=True,  # Memory mapping for better performance
            use_mlock=False,  # Don't lock memory (can cause issues on some systems)
        )
        
        load_time = time.time() - start_time
        print(f"Model loaded in {load_time:.2f} seconds")
    
    def generate_response(self, 
                         prompt: str, 
                         max_tokens: int = 1000,
                         temperature: float = 0.7,
                         top_p: float = 0.9,
                         top_k: int = 40,
                         repeat_penalty: float = 1.1,
                         stream: bool = False) -> str:
        """
        Generate response from the model
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.1-2.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repeat_penalty: Penalty for repetition
            stream: Whether to stream output
        """
        
        # Format prompt for better biomedical responses
        formatted_prompt = f"Question: {prompt}\nAnswer:"
        
        start_time = time.time()
        
        if stream:
            print("Response: ", end="", flush=True)
            response_text = ""
            for output in self.llm(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stream=True,
                stop=["Question:", "\n\n"]
            ):
                token = output['choices'][0]['text']
                print(token, end="", flush=True)
                response_text += token
            print()  # New line after streaming
            return response_text.strip()
        else:
            output = self.llm(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=["Question:", "\n\n"]
            )
            
            response = output['choices'][0]['text'].strip()
            generation_time = time.time() - start_time
            tokens_generated = len(self.llm.tokenize(response.encode()))
            tokens_per_second = tokens_generated / generation_time if generation_time > 0 else 0
            
            print(f"Generated {tokens_generated} tokens in {generation_time:.2f}s ({tokens_per_second:.1f} tokens/s)")
            return response
    
    def chat_loop(self):
        """Interactive chat loop"""
        print("\n🧬 BioGPT Chat Interface")
        print("Type 'quit', 'exit', or 'q' to end the conversation")
        print("Type 'stream' to toggle streaming mode")
        print("=" * 50)
        
        stream_mode = False
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if user_input.lower() == 'stream':
                    stream_mode = not stream_mode
                    print(f"Streaming mode {'enabled' if stream_mode else 'disabled'}")
                    continue
                
                if not user_input:
                    continue
                
                print(f"\nBioGPT: ", end="" if stream_mode else "\n")
                response = self.generate_response(user_input, stream=stream_mode)
                
                if not stream_mode:
                    print(response)
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    # Installation instructions
    print("=" * 60)
    print("SETUP INSTRUCTIONS:")
    print("=" * 60)
    print("1. Install required packages:")
    print("   pip install llama-cpp-python requests tqdm")
    print("\n2. The script will automatically download the BioGPT Q5_K_M model")
    print("   Model size: ~800MB (higher quality)")
    print("=" * 60)
    
    print(f"\n📋 Using: biogpt-baseline.Q5_K_M.gguf")
    print(f"📏 Size: ~800MB (higher quality)")
    
    try:
        # Download the model
        model_path = download_model()
        
        # Initialize the model
        print(f"\n🚀 Initializing BioGPT...")
        bot = BioGPTChat(model_path, n_ctx=2048)
        
        # Example usage
        print("\n🧪 Testing with biomedical example:")
        test_prompt = "What are the steps to help someone having a heart attack?"
        response = bot.generate_response(test_prompt)
        print(f"Prompt: {test_prompt}")
        print(f"Response: {response}")
        
        # Start interactive chat
        bot.chat_loop()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have internet connection")
        print("2. Install required packages: pip install llama-cpp-python requests tqdm")
        print("3. Check if you have enough disk space")

if __name__ == "__main__":
    main()