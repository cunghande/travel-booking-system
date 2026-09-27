# ============================================================
# Travel Booking System — Demo Data Seeder
# ============================================================
from __future__ import annotations

import asyncio
import uuid
from datetime import date, time

from loguru import logger
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.domain.entities.booking import Booking, BookingPassenger
from app.domain.entities.tour import Itinerary, ItineraryActivity, Tour
from app.domain.entities.user import Role, User
from app.domain.value_objects.enums import BookingStatus, RoleName, TourStatus
from app.infrastructure.db.session import async_session_factory


async def get_role(session, name):
    result = await session.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()


async def get_or_create_user(session, email, full_name, password, role_name):
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        logger.info("User already exists: {}", email)
        return user
    role = await get_role(session, role_name)
    user = User(email=email, full_name=full_name, hashed_password=hash_password(password), is_active=True)
    if role:
        user.roles = [role]
    session.add(user)
    await session.flush()
    logger.info("Created user: {} ({})", email, role_name)
    return user


def make_tour(tour_code, title, description, category, tags, destination, price_adult, price_child,
              max_participants, available_slots, start_date, end_date, status, created_by, itineraries_data):
    tour = Tour(tour_code=tour_code, title=title, description=description, category=category, tags=tags,
                destination=destination, base_price_adult=price_adult, base_price_child=price_child,
                max_participants=max_participants, available_slots=available_slots,
                start_date=start_date, end_date=end_date, status=status, created_by=created_by)
    for itin_data in itineraries_data:
        itin = Itinerary(day_number=itin_data['day'], title=itin_data['title'])
        for act in itin_data.get('activities', []):
            itin.activities.append(ItineraryActivity(
                time=act.get('time'), place_name=act['place'],
                latitude=act.get('lat'), longitude=act.get('lng'), description=act.get('desc')))
        tour.itineraries.append(itin)
    return tour


async def seed_demo(session):
    staff = await get_or_create_user(session, 'staff@travelbooking.com', 'Nguyen Van Staff', 'Staff@123456', RoleName.STAFF.value)
    customer1 = await get_or_create_user(session, 'customer1@example.com', 'Tran Thi Lan', 'Customer@123456', RoleName.CUSTOMER.value)
    customer2 = await get_or_create_user(session, 'customer2@example.com', 'Le Van Hung', 'Customer@123456', RoleName.CUSTOMER.value)
    customer3 = await get_or_create_user(session, 'customer3@example.com', 'Pham Thi Mai', 'Customer@123456', RoleName.CUSTOMER.value)

    existing_codes = set((await session.execute(select(Tour.tour_code))).scalars().all())

    tours_raw = [
        ('TOUR-HN-001', 'Ha Noi - Ha Long 3 Days 2 Nights', 'Cruise on Ha Long Bay - UNESCO World Heritage. Sleep on 5-star cruise, kayaking, cave exploring.', 'Bien dao', ['ha long','cruise','seafood'], 'Ha Long, Quang Ninh', 3500000, 2100000, 30, 22, date(2027,1,15), date(2027,1,17), TourStatus.PUBLISHED.value,
         [{'day':1,'title':'Ha Noi to Ha Long Bay','activities':[{'time':time(7,30),'place':'Ha Noi departure','lat':21.0285,'lng':105.8542,'desc':'Board bus to Ha Long'},{'time':time(11,30),'place':'Tuan Chau Port','lat':20.9317,'lng':107.0028,'desc':'Board cruise, lunch'},{'time':time(14,0),'place':'Sung Sot Cave','lat':20.8795,'lng':107.0873,'desc':'Visit amazing cave'},{'time':time(17,0),'place':'Cua Van Floating Village','lat':20.8621,'lng':107.1345,'desc':'Explore fishing village'}]},
          {'day':2,'title':'Kayaking - Swimming - Ti Top Island','activities':[{'time':time(6,30),'place':'Ship Deck','desc':'Sunrise yoga'},{'time':time(9,0),'place':'Ti Top Island','lat':20.8764,'lng':107.0931,'desc':'Hiking, swimming, kayaking'},{'time':time(14,0),'place':'Luon Cave','lat':20.9012,'lng':107.1203,'desc':'Kayak through cave'},{'time':time(19,0),'place':'Restaurant on ship','desc':'Dinner party'}]},
          {'day':3,'title':'Morning return to Ha Noi','activities':[{'time':time(7,0),'place':'Ship deck','desc':'Breakfast, pack'},{'time':time(9,0),'place':'Tuan Chau Port','desc':'Disembark'},{'time':time(10,0),'place':'Bus back to Ha Noi','desc':'Return journey'}]}]),
        ('TOUR-DN-002', 'Da Nang - Hoi An - Ba Na Hills 4 Days', 'Central Vietnam: ancient Hoi An lantern town, Golden Bridge at Ba Na Hills, My Khe beach.', 'Van hoa', ['hoi an','ba na hills','golden bridge'], 'Da Nang - Hoi An', 5200000, 3100000, 25, 18, date(2027,2,5), date(2027,2,8), TourStatus.PUBLISHED.value,
         [{'day':1,'title':'Arrive Da Nang - Ba Na Hills','activities':[{'time':time(10,0),'place':'Da Nang Airport','lat':16.0443,'lng':108.1992,'desc':'Pick up guests'},{'time':time(13,0),'place':'Ba Na Hills','lat':15.9973,'lng':107.9895,'desc':'Golden Bridge, cable car'},{'time':time(19,0),'place':'Hotel Da Nang','desc':'Check in, dinner'}]},
          {'day':2,'title':'Hoi An Ancient Town','activities':[{'time':time(8,0),'place':'Hoi An Ancient Town','lat':15.8801,'lng':108.338,'desc':'Japanese Bridge, old houses'},{'time':time(18,0),'place':'Hoai River','desc':'Lantern floating ceremony'}]},
          {'day':3,'title':'My Khe Beach - Marble Mountains','activities':[{'time':time(8,0),'place':'My Khe Beach','lat':16.0626,'lng':108.2468,'desc':'Morning swim'},{'time':time(14,0),'place':'Marble Mountains','lat':16.0024,'lng':108.2649,'desc':'Climb, caves, pagodas'}]},
          {'day':4,'title':'Free morning - Fly home','activities':[{'time':time(11,0),'place':'Da Nang Airport','desc':'Fly home'}]}]),
        ('TOUR-SG-003', 'Sai Gon - Mui Ne - Phan Thiet 3 Days', 'Escape the city: white sand dunes, fairy stream, fresh seafood at the beach.', 'Nghi duong', ['mui ne','sand dunes','seafood'], 'Mui Ne, Binh Thuan', 2800000, 1680000, 40, 35, date(2027,1,25), date(2027,1,27), TourStatus.PUBLISHED.value,
         [{'day':1,'title':'HCMC to Mui Ne','activities':[{'time':time(7,0),'place':'Mien Dong Bus Station','lat':10.8142,'lng':106.7086,'desc':'Depart to Mui Ne'},{'time':time(13,0),'place':'Red Sand Dunes','lat':10.9279,'lng':108.2892,'desc':'Sand sledding, sunset'},{'time':time(17,30),'place':'Mui Ne Beach','desc':'Check in resort'}]},
          {'day':2,'title':'White Dunes Sunrise - Fairy Stream','activities':[{'time':time(5,30),'place':'White Sand Dunes','desc':'Sunrise on dunes'},{'time':time(9,0),'place':'Fairy Stream','lat':10.9534,'lng':108.2742,'desc':'Walk through stream'},{'time':time(13,0),'place':'Seafood Market','desc':'Fresh grilled seafood'}]},
          {'day':3,'title':'Fishing Village - Return HCMC','activities':[{'time':time(7,0),'place':'Mui Ne Fishing Village','desc':'Watch fishermen, buy dried seafood'},{'time':time(12,0),'place':'Bus to HCMC','desc':'Return'}]}]),
        ('TOUR-SP-004', 'Sapa - Fansipan - Cat Cat Village 4 Days', 'Conquer Fansipan 3143m, terraced rice fields, H Mong villages.', 'Trekking', ['fansipan','sapa','trekking','rice fields'], 'Sapa, Lao Cai', 4100000, 2460000, 20, 14, date(2027,3,10), date(2027,3,13), TourStatus.PUBLISHED.value,
         [{'day':1,'title':'Hanoi to Sapa by night train','activities':[{'time':time(21,30),'place':'Hanoi Station','lat':21.0245,'lng':105.8412,'desc':'Board night train'}]},
          {'day':2,'title':'Cat Cat Village - Sapa Town','activities':[{'time':time(5,30),'place':'Lao Cai Station','lat':22.5058,'lng':103.9753,'desc':'Transfer to Sapa'},{'time':time(9,0),'place':'Cat Cat Village','lat':22.3341,'lng':103.8352,'desc':'H Mong village, waterfall'},{'time':time(18,0),'place':'Sapa Night Market','desc':'Local wine and food'}]},
          {'day':3,'title':'Conquer Fansipan','activities':[{'time':time(7,0),'place':'Fansipan Cable Car Station','lat':22.3305,'lng':103.8195,'desc':'Cable car up Fansipan'},{'time':time(9,0),'place':'Fansipan Summit','lat':22.3033,'lng':103.7759,'desc':'3143m highest peak in Indochina'},{'time':time(15,0),'place':'Muong Hoa Terraced Fields','desc':'Golden rice terraces'}]},
          {'day':4,'title':'Return to Hanoi','activities':[{'time':time(10,0),'place':'Lao Cai Station','desc':'Train back to Hanoi'}]}]),
        ('TOUR-PHQ-005', 'Phu Quoc Island 5 Days 4 Nights', 'Vietnam Maldives: snorkeling, fish safari, VinWonders, famous fish sauce factory.', 'Bien dao nghi duong', ['phu quoc','snorkeling','coral','vinwonders'], 'Phu Quoc, Kien Giang', 7500000, 4500000, 20, 12, date(2027,4,1), date(2027,4,5), TourStatus.PUBLISHED.value,
         [{'day':1,'title':'Fly to Phu Quoc - Sao Beach','activities':[{'time':time(8,0),'place':'Phu Quoc International Airport','lat':10.227,'lng':103.9673,'desc':'Pickup'},{'time':time(14,0),'place':'Sao Beach','lat':10.0113,'lng':103.9973,'desc':'Swim at the most beautiful beach'}]},
          {'day':2,'title':'Snorkeling - Fishing','activities':[{'time':time(7,30),'place':'An Thoi Port','lat':10.0063,'lng':104.0196,'desc':'Board boat'},{'time':time(9,0),'place':'Hon Thom Island','lat':9.9988,'lng':104.0253,'desc':'Snorkeling, fishing'}]},
          {'day':3,'title':'VinWonders - Safari','activities':[{'time':time(9,0),'place':'VinWonders Phu Quoc','lat':10.3481,'lng':103.8433,'desc':'Water park and rides'},{'time':time(14,0),'place':'Vinpearl Safari','lat':10.3632,'lng':103.8285,'desc':'Wildlife safari'}]},
          {'day':4,'title':'Ham Ninh Fishing Village - Fish Sauce Factory','activities':[{'time':time(8,0),'place':'Ham Ninh Village','desc':'Fresh crab and seafood'},{'time':time(14,0),'place':'Fish Sauce Factory','desc':'Traditional fish sauce process'},{'time':time(17,30),'place':'Dinh Cau','desc':'Sunset watch point'}]},
          {'day':5,'title':'Free morning - Fly home','activities':[{'time':time(14,0),'place':'Phu Quoc Airport','desc':'Fly home'}]}]),
        ('TOUR-NTR-006', 'Nha Trang - Binh Ba Island 4 Days', 'Vibrant beach city: Vinpearl Land, lobster island Binh Ba, Po Nagar Cham towers.', 'Bien dao', ['nha trang','vinpearl','lobster','binh ba'], 'Nha Trang, Khanh Hoa', 4600000, 2760000, 35, 28, date(2027,2,20), date(2027,2,23), TourStatus.PUBLISHED.value,
         [{'day':1,'title':'Arrive Nha Trang - Cham Towers','activities':[{'time':time(10,0),'place':'Cam Ranh Airport','lat':11.9983,'lng':109.2193,'desc':'Pickup'},{'time':time(14,0),'place':'Po Nagar Cham Towers','lat':12.2646,'lng':109.1934,'desc':'Ancient Cham temple'},{'time':time(16,0),'place':'Nha Trang Beach','lat':12.2388,'lng':109.1967,'desc':'Beach time'}]},
          {'day':2,'title':'Vinpearl Land - Hon Tre Island','activities':[{'time':time(8,0),'place':'Vinpearl Cable Car','lat':12.2251,'lng':109.2023,'desc':'Worlds longest over-sea cable car'},{'time':time(9,0),'place':'Vinpearl Land','lat':12.2114,'lng':109.2041,'desc':'Water park, rides'}]},
          {'day':3,'title':'Binh Ba Island - Grilled Lobster','activities':[{'time':time(7,0),'place':'Binh Ba Port','desc':'Boat to Binh Ba Island'},{'time':time(11,0),'place':'Binh Ba Island','lat':11.7556,'lng':109.1997,'desc':'Swim, snorkel, grilled lobster'}]},
          {'day':4,'title':'Mud Bath Spa - Dam Market - Fly home','activities':[{'time':time(8,0),'place':'Mud Bath Spa','desc':'Mineral mud bath'},{'time':time(12,0),'place':'Dam Market','desc':'Buy dried squid, bird nest, local goods'},{'time':time(15,0),'place':'Cam Ranh Airport','desc':'Fly home'}]}]),
    ]

    created_tours = []
    for td in tours_raw:
        code = td[0]
        if code in existing_codes:
            result = await session.execute(select(Tour).where(Tour.tour_code == code))
            tour = result.scalar_one()
            logger.info("Tour exists: {}", code)
        else:
            tour = make_tour(code, td[1], td[2], td[3], td[4], td[5], td[6], td[7],
                             td[8], td[9], td[10], td[11], td[12], staff.id, td[13])
            session.add(tour)
            await session.flush()
            logger.info("Created tour: {}", code)
        created_tours.append(tour)

    count = (await session.execute(select(sqlfunc.count(Booking.id)))).scalar()
    if count and count > 0:
        logger.info("Bookings already exist ({}). Skipping.", count)
    else:
        bookings = [
            Booking(booking_code='BK-20270101-HL01', user_id=customer1.id, tour_id=created_tours[0].id,
                    status=BookingStatus.CONFIRMED, num_adults=2, num_children=1,
                    total_price=2*3500000+1*2100000, contact_name='Tran Thi Lan',
                    contact_email='customer1@example.com', contact_phone='0901234567',
                    special_requests='Sea view room, vegetarian day 2'),
            Booking(booking_code='BK-20270102-DN01', user_id=customer2.id, tour_id=created_tours[1].id,
                    status=BookingStatus.PENDING_PAYMENT, num_adults=2, num_children=0,
                    total_price=2*5200000, contact_name='Le Van Hung',
                    contact_email='customer2@example.com', contact_phone='0912345678'),
            Booking(booking_code='BK-20270103-MN01', user_id=customer3.id, tour_id=created_tours[2].id,
                    status=BookingStatus.CONFIRMED, num_adults=3, num_children=2,
                    total_price=3*2800000+2*1680000, contact_name='Pham Thi Mai',
                    contact_email='customer3@example.com', contact_phone='0923456789',
                    special_requests='Need wheelchair for 1 person'),
            Booking(booking_code='BK-20270104-SP01', user_id=customer1.id, tour_id=created_tours[3].id,
                    status=BookingStatus.CANCELLED, num_adults=1, num_children=0,
                    total_price=4100000, contact_name='Tran Thi Lan',
                    contact_email='customer1@example.com', contact_phone='0901234567'),
            Booking(booking_code='BK-20270105-PQ01', user_id=customer2.id, tour_id=created_tours[4].id,
                    status=BookingStatus.CONFIRMED, num_adults=2, num_children=1,
                    total_price=2*7500000+4500000, contact_name='Le Van Hung',
                    contact_email='customer2@example.com', contact_phone='0912345678',
                    special_requests='Honeymoon room if available'),
        ]
        passengers_map = {
            0: [BookingPassenger(full_name='Tran Thi Lan', passenger_type='ADULT', id_card_number='001234567890'),
                BookingPassenger(full_name='Tran Van Nam', passenger_type='ADULT', id_card_number='001234567891'),
                BookingPassenger(full_name='Tran Be An', passenger_type='CHILD')],
            1: [BookingPassenger(full_name='Le Van Hung', passenger_type='ADULT', id_card_number='002345678901'),
                BookingPassenger(full_name='Nguyen Thi Hoa', passenger_type='ADULT', id_card_number='002345678902')],
            2: [BookingPassenger(full_name='Pham Thi Mai', passenger_type='ADULT', id_card_number='003456789012'),
                BookingPassenger(full_name='Pham Van Binh', passenger_type='ADULT'),
                BookingPassenger(full_name='Nguyen Anh Dung', passenger_type='ADULT'),
                BookingPassenger(full_name='Pham Be Thao', passenger_type='CHILD'),
                BookingPassenger(full_name='Pham Be Nam', passenger_type='CHILD')],
            3: [BookingPassenger(full_name='Tran Thi Lan', passenger_type='ADULT', id_card_number='001234567890')],
            4: [BookingPassenger(full_name='Le Van Hung', passenger_type='ADULT', id_card_number='002345678901'),
                BookingPassenger(full_name='Nguyen Thi Hoa', passenger_type='ADULT', id_card_number='002345678902'),
                BookingPassenger(full_name='Le Be Yen', passenger_type='CHILD')],
        }
        for i, b in enumerate(bookings):
            b.passengers = passengers_map[i]
            session.add(b)
        await session.flush()
        logger.info("Created 5 sample bookings")

    await session.commit()
    logger.info("Demo seed done!")


async def run():
    logger.info("Starting demo seed...")
    async with async_session_factory() as session:
        try:
            await seed_demo(session)
        except Exception as e:
            await session.rollback()
            logger.error("Failed: {}", e)
            raise

if __name__ == '__main__':
    asyncio.run(run())
