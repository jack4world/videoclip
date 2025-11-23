"""
检查 DashScope API 配置和配额状态
"""
import dashscope
from dashscope import Models

from videoclip.config import get_settings
from videoclip.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

def check_api_config():
    """检查 API 配置"""
    settings = get_settings()
    
    if not settings.qwen_api_key:
        logger.error("❌ 未找到 QWEN_API_KEY 环境变量")
        logger.error("   请在 .env 文件中设置 QWEN_API_KEY")
        return False
    
    logger.info("✓ API Key 已配置")
    logger.info(f"  Key 前缀: {settings.qwen_api_key[:10]}...")
    
    # 设置 API Key
    dashscope.api_key = settings.qwen_api_key
    
    # 尝试列出可用模型（这是一个简单的 API 调用，用于测试）
    try:
        logger.info("\n正在检查 API 连接和配额...")
        result = Models.list()
        
        if result.status_code == 200:
            logger.info("✓ API 连接成功")
            logger.info("✓ 账户状态正常")
            return True
        else:
            logger.warning(f"⚠ API 返回状态码: {result.status_code}")
            if hasattr(result, 'message'):
                logger.warning(f"  消息: {result.message}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ API 检查失败: {error_msg}")
        
        if 'quota' in error_msg.lower() or 'Throttling' in error_msg:
            logger.warning("\n⚠ 配额相关错误：")
            logger.warning("   1. 请确认使用的是付费账户的 API Key")
            logger.warning("   2. 访问 https://dashscope.console.aliyun.com/ 检查配额")
            logger.warning("   3. 如果是新账户，可能需要等待配额生效")
        elif '401' in error_msg or 'Unauthorized' in error_msg:
            logger.warning("\n⚠ 认证错误：")
            logger.warning("   1. 请检查 API Key 是否正确")
            logger.warning("   2. 确认 API Key 是否已激活")
        
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("DashScope API 配置检查")
    print("=" * 60)
    print()
    
    if check_api_config():
        print("\n" + "=" * 60)
        print("✓ 配置检查通过，可以开始使用")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 配置检查失败，请根据上述提示修复问题")
        print("=" * 60)
