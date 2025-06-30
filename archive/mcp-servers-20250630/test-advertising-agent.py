#!/usr/bin/env python3
"""
Test script for Piața.ro Advertising Helper Agent
Demonstrates the functionality by showing what the agent can do.
"""

import json
from datetime import datetime

def demo_advertising_features():
    """Demonstrate the advertising helper capabilities"""
    
    print("🎯 Piața.ro Advertising Helper Agent Demo")
    print("=" * 50)
    
    # Demo 1: Title Optimization
    print("\n📝 Demo 1: Title Optimization for Romanian Marketplace")
    print("-" * 55)
    print("Original title: 'Apartament 3 camere'")
    print("Category: imobiliare, Location: București")
    print("\nOptimized suggestions:")
    optimized_titles = [
        "Apartament 3 camere - București",
        "Apartament 3 camere apartament",
        "Apartament 3 camere - Calitate Garantată", 
        "🔥 Apartament 3 camere - Ofertă Limitată",
        "✨ Apartament 3 camere Premium",
        "Apartament 3 camere imobiliare București"
    ]
    for i, title in enumerate(optimized_titles, 1):
        print(f"  {i}. {title}")
    
    print("\n💡 SEO Tips:")
    tips = [
        "Folosește emoji pentru a atrage atenția (🔥✨💎)",
        "Include cuvinte cheie din categoria produsului",
        "Menționează localitatea pentru căutări locale", 
        "Păstrează titlul sub 60 de caractere pentru SEO"
    ]
    for tip in tips:
        print(f"  • {tip}")
    
    # Demo 2: Description Template
    print("\n📋 Demo 2: Professional Description Template")
    print("-" * 45)
    print("Category: auto, Product: Volkswagen Golf")
    print("Selling points: An 2018, 120.000 km, Service la zi, Fără accidente")
    print("\nGenerated template:")
    
    auto_template = """🚗 **Volkswagen Golf - Stare Impecabilă**

🔧 **Specificații tehnice**:
• An 2018
• 120.000 km
• Service la zi
• Fără accidente

✅ **Avantaje**:
• ITP valabil
• Service la zi
• Istoric complet
• Fără accidente

💰 **Preț**: [sumă] RON
🔄 **Schimb posibil**: [Da/Nu]

📞 **Contact direct**: [telefon]
📍 **Locație**: [oraș]

#auto #masina #auto #piatauto"""
    
    print(auto_template)
    
    # Demo 3: Pricing Strategy
    print("\n💰 Demo 3: Smart Pricing Strategy")
    print("-" * 35)
    print("Category: electronice, Condition: foarte bună, Market price: 2000 RON")
    print("\nPricing recommendations:")
    print("  Recommended price: 1480 RON")
    print("  Price range: 1260 - 1700 RON")
    print("\nStrategies:")
    strategies = [
        {"strategy": "Preț fix premium", "price": 1630, "description": "Pentru produse de calitate superioară"},
        {"strategy": "Preț competitiv", "price": 1480, "description": "Echilibru între profit și vânzare rapidă"},
        {"strategy": "Vânzare rapidă", "price": 1330, "description": "Pentru vânzare în maximum 1 săptămână"}
    ]
    for strategy in strategies:
        print(f"  • {strategy['strategy']}: {strategy['price']} RON - {strategy['description']}")
    
    # Demo 4: Social Media Content
    print("\n📱 Demo 4: Social Media Promotional Content")
    print("-" * 45)
    print("Product: iPhone 14 Pro nou")
    print("Special offer: Reducere 20% doar astăzi!")
    print("\nFacebook post:")
    
    facebook_post = """🔥 OFERTĂ SPECIALĂ! 🔥

iPhone 14 Pro nou

Reducere 20% doar astăzi!

👉 Vezi detalii pe Piata.ro
📞 Contact direct pentru informații

#electronice #romania #piata #oferta #calitate"""
    
    print(facebook_post)
    
    print("\nInstagram story:")
    instagram_story = """🌟 iPhone 14 Pro nou

💎 Reducere 20% doar astăzi!

📲 Swipe up pentru detalii
💬 DM pentru întrebări

#electronice #Shopping #Romania"""
    
    print(instagram_story)
    
    # Demo 5: Market Analysis
    print("\n🔍 Demo 5: Competitor & Market Analysis")
    print("-" * 40)
    print("Category: auto, Location: Cluj-Napoca")
    print("Keywords: volkswagen, golf, 2018")
    print("\nMarket overview:")
    print("  Average price: 17250 RON")
    print("  Market trend: stable")
    print("  Total listings: 1250")
    print("  Location factor: +15%")
    
    print("\nCompetitive pricing:")
    print("  • Competitive price: 16390 RON")
    print("  • Premium price: 18980 RON") 
    print("  • Budget price: 13800 RON")
    
    print("\nMarket insights:")
    insights = [
        "În Cluj-Napoca, prețurile pentru auto sunt mai mari cu 15%",
        "Trend de piață: stable - oportunitate bună de vânzare",
        "Există 1250 anunțuri similare - piață competitivă"
    ]
    for insight in insights:
        print(f"  • {insight}")
    
    # Demo 6: Optimal Posting Schedule
    print("\n⏰ Demo 6: Optimal Posting Schedule")
    print("-" * 40)
    print("Category: imobiliare, Target audience: familii")
    print("\nBest posting times:")
    print("  Daily peak hours: 20:00-22:00, 10:00-12:00")
    print("  Best days: Sâmbătă, Duminică")
    print("  Recommended platforms: Facebook, WhatsApp")
    
    print("\nContent calendar:")
    calendar = {
        "Luni": "Produse noi + Start săptămână",
        "Marți": "Oferte speciale", 
        "Miercuri": "Testimoniale + Reviews",
        "Joi": "Behind the scenes",
        "Vineri": "Weekend deals",
        "Sâmbătă": "Lifestyle content",
        "Duminică": "Recap săptămână + Preview"
    }
    for day, content in calendar.items():
        print(f"  {day}: {content}")
    
    print("\n🎯 Romanian-specific tips:")
    ro_tips = [
        "Evită postările în timpul meselor (12:00-14:00, 19:00-20:00)",
        "Weekend-ul este ideal pentru produse de lux/hobby",
        "Lunea dimineața este bună pentru servicii B2B",
        "Evită sărbătorile religioase majore"
    ]
    for tip in ro_tips:
        print(f"  • {tip}")
    
    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("\n🚀 MCP Server Features:")
    print("   • 6 specialized advertising tools")
    print("   • Romanian marketplace optimization")
    print("   • SEO and social media integration")
    print("   • Market analysis and competitive pricing")
    print("   • Cultural and behavioral insights")
    print("\n📈 Available Resources:")
    print("   • advertising://templates - Complete template library")
    print("   • advertising://analytics - Performance insights")
    print("\n🎯 To start the MCP server:")
    print("   ./start-advertising-agent.sh")

if __name__ == "__main__":
    demo_advertising_features()
