import os
from datetime import datetime
import functions
import constants
import requests
from openai import OpenAI
import json

def main():

    # Fetching astrology API credentials from AWS secrets manager
    secret_name = 'astrotech/astrology_api_key'
    region_name = 'ap-south-1'
    username, password = functions.get_astrology_credentials(secret_name=secret_name, region_name=region_name)
    
    # Calling monthly Horoscope API
    # https://json.astrologyapi.com/v1/horoscope_prediction/monthly/:zodiacName
    # url = f"{constants.ASTROLOGY_API_URL}/horoscope_prediction/monthly/aries"
    # Send the request
    # response = requests.post(url, auth=(username, password))

    sun_signs = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces"] 
   
    category_prediction = {
    
    "love": "In the realm of love, Venus, the planet of affection, dances through your 7th House of Partnership from late September to mid-October. This alignment fosters a warm ambiance ripe for romance, rejuvenation of relationships, and deeper understanding. This period is particularly rich for single Taureans scouting for genuine connections and those in relationships looking to reignite passion. Dates like 5, 8, 15, 16, and 17 October are pivotal — perfect for nurturing bonds and open communication. A New Moon on 1 November hints at a fresh chapter in your love life, sprinkled with hope and deeper bonding.",
    "travel": "Your travel stars have been in flux since Pluto’s stay in your 9th House since 2008. As it prepares to exit in November 2024, the universe nudges you to embark on new journeys. The early months, especially January and February, beckon with possibilities of long vacations, academic pursuits, or work-related adventures. This year, exploration, both external and of the self, is a significant theme. By November, a sense of nostalgia might pull you back to a previously visited place, a testament to the year’s emphasis on revisiting and redefining. Stay open, embrace spontaneity, and let every journey, whether physical or emotional, bring a fresh perspective.",
    "career": "Financial stability and growth lie at the forefront in 2024. Jupiter’s gracious transition into Gemini from late May is a harbinger of prosperity. This movement illuminates opportunities not just to enhance wealth but to bolster self-worth and confidence in professional realms. With Jupiter’s benevolent gaze, negotiations for contracts, salaries, or new ventures receive a cosmic push, especially around 3 June. Mars infuses energy into your financial pursuits from July to September. This phase is golden for Taureans looking to make bold financial moves, invest wisely, or restructure their economic landscape. It’s a year where financial acumen is not just about numbers but about self-belief.",
    "health": "Holistic well-being will be emphasized in 2024. The 12th House is buzzing, urging a balance between the external hustle and inner tranquillity. Two significant eclipses, a New Moon in April and a Full Moon in October, draw attention to rest and rejuvenation. Mars’ journey through Aries between May and June signals a potential dip in vitality. Herein lies a reminder to embrace practices that nourish the soul. Spiritual modalities, especially heated yoga sessions or meditation in infra-red saunas, emerge as potent tools for mental and physical rejuvenation. They aren’t just exercises but profound experiences that connect you deeper to your essence. Remember, as life’s demands fluctuate, it’s imperative to retreat, recharge, and return stronger.",
    "emotions": "Challenges are but stepping stones, and 2024 brings its set of hurdles. The North Node in Aries is a beacon, advocating for introspection and spiritual grounding. In testing times, leaning into meditation, guided spiritual practices, or even simple mindfulness exercises can provide solace. The warmth of Bikram yoga or the serene silence of an infra-red sauna can be transformative. Additionally, tapping into Taurean resilience and seeking guidance from spiritual mentors or trusted counselors can provide clarity. Eclipses, particularly in April and October, underscore the essence of self-care. They serve as cosmic reminders that true strength is balancing doing with being. As challenges arise, remember that the cosmos has equipped you with a spiritual toolkit; it’s just a matter of accessing it."
    
    }

    defualt_response = {
        "status": True,
        "sun_sign": "aries",
        "prediction_month": "January",
        "prediction": [
            "This is an ideal way to start the New Year as Aries have their planet Mars in the first house and so while Mars will encounter stiff opposition from the big heavies Pluto and Saturn by square, as it passes through your first house, you will have the energy to handle the questions these planets will ask of your commitment and strength.",
            "This is not a time for frivolous goals, these will quickly go by the wayside, this is a time when your most important goals must become your priority.",
            "You feel a great call to action and yet you sense that what you are setting up for will require commitment and will test your character. The powers that be in your life will resist what you intend, you should bear in mind that the very people you may respect or defer to could be the same people that now want to stand in your way and you now need to review your relationship with them.",
            "If you are happy with the course you are on, the effect of Jupiter will reinforce what you are doing adding energy and some luck at critical moments; if you have been struggling, this can be a time where you are more at peace with the unchangeable circumstances and have faith that you will prevail eventually.",
            "Aries are very open, this means that in relationships you are eager to share your deeper feelings and fears and that opens the gateway to some substantial sharing and progresses.  Things get psychologically intimate quite quickly and in new love affairs you may find that similar family backgrounds or similar experience (good and bad) with parents draw you to a person and cement a bond.",
            "It is a time of positive experiences with others, not just in terms of having fun superficially but in terms of meaningful interaction and reaches the deeper parts of you. Much of what is good in love happens not so much in terms of external experience, but in terms of the affect a new person in your life has on you internally, they may just spark something or reawaken an energy you had not felt for some time."
        ]
    }

    for sun_sign in sun_signs:

        print(f"Processing for sun sign: {sun_sign}")
        response = defualt_response
        response['sun_sign'] = sun_sign
        
        for key, value in category_prediction.items():
            response[key] = value

        data_dict = json.loads(json.dumps(response))

        # Loading the data into mangoDB
        functions.load_monthly_horoscope_to_mongodb(data_dict, 'horoscope_monthly')

    print(f'Job completed successfully')

if __name__ == "__main__":
    main()