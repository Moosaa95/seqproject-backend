from django.core.management.base import BaseCommand
from api.models import Agent, Property, PropertyImage, Location
import random

class Command(BaseCommand):
    help = 'Adds 20+ sample properties with locations and images to the database'

    def handle(self, *args, **kwargs):
        # Create or get agents
        agents_data = [
            {
                'name': 'Tijjani Musa',
                'phone': '(222) 456-8932',
                'mobile': '777 287 378 737',
                'email': 'tijjani@seqprojects.com'
            },
            {
                'name': 'Aminu Ibrahim',
                'phone': '(234) 803-456-7890',
                'mobile': '803 456 7890',
                'email': 'aminu@seqprojects.com'
            },
            {
                'name': 'Fatima Mohammed',
                'phone': '(234) 805-123-4567',
                'mobile': '805 123 4567',
                'email': 'fatima@seqprojects.com'
            },
            {
                'name': 'Chidi Okafor',
                'phone': '(234) 807-890-1234',
                'mobile': '807 890 1234',
                'email': 'chidi@seqprojects.com'
            }
        ]

        agents = []
        for agent_data in agents_data:
            agent, created = Agent.objects.get_or_create(
                email=agent_data['email'],
                defaults=agent_data
            )
            agents.append(agent)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created agent: {agent.name}'))

        # Location data
        location_names = [
            'Wuse Zone 1', 'Wuse Zone 2', 'Maitama', 'Asokoro', 'Gwarimpa',
            'Jabi', 'Garki', 'Katampe', 'Kado', 'Lifecamp',
            'Jahi', 'Kubwa', 'Dutse', 'Lokogoma', 'Gudu'
        ]
        
        locations_map = {}
        for name in location_names:
            loc, _ = Location.objects.get_or_create(name=name, defaults={'address': f"{name}, Abuja"})
            locations_map[name] = loc

        property_types = ['Apartment', 'Villa', 'Duplex', 'Penthouse', 'Terrace', 'Bungalow']

        entities = [
            'Sequoia Projects Ltd',
            'Arusha Property Management',
            'Jacobs Bay Real Estate',
            'Prime Properties Abuja',
            'Elite Homes Nigeria'
        ]

        amenities_options = [
            ['WiFi', '24/7 Electricity', 'Security', 'Parking', 'Water Supply'],
            ['Swimming Pool', 'Gym', 'WiFi', 'Security', '24/7 Electricity', 'Parking'],
            ['Fully Equipped Kitchen', 'Air Conditioning', 'WiFi', 'Security', 'Parking'],
            ['Garden', 'BBQ Area', 'Parking', 'Security', '24/7 Electricity', 'WiFi'],
            ['Elevator', 'Security', 'Parking', 'WiFi', '24/7 Electricity', 'Backup Generator'],
            ['Serviced', 'WiFi', '24/7 Electricity', 'Water Supply', 'Security', 'Parking'],
            ['Pool', 'Gym', 'Security', 'WiFi', 'Parking', 'Playground'],
        ]
        
        # Sample property images (Using generic placeholder/architectural URLs)
        image_urls = [
            "https://images.unsplash.com/photo-1600596542815-22b5db05163c?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600607687644-c7171b42498f?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600573472993-90e8c27cf967?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=800&q=80",
             "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=800&q=80",
             "https://images.unsplash.com/photo-1515263487990-61b07816b324?auto=format&fit=crop&w=800&q=80"
        ]

        properties_data = [
            # Luxury properties (First 5)
            {
                'title': 'Luxury 5-Bedroom Villa with Pool',
                'type': 'Villa', 'bedrooms': 5, 'bathrooms': 6, 'living_rooms': 2, 'garages': 2, 'guests': 10,
                'status': 'sale', 'price': 450000000,
                'description': 'Stunning luxury villa in the heart of Maitama. Features include a private pool, modern kitchen...',
                'featured': True, 'loc_name': 'Maitama'
            },
            {
                'title': 'Executive 4-Bedroom Penthouse',
                'type': 'Penthouse', 'bedrooms': 4, 'bathrooms': 5, 'living_rooms': 2, 'garages': 2, 'guests': 8,
                'status': 'rent', 'price': 2500000,
                'description': 'Breathtaking penthouse with panoramic views. Modern finishes...',
                'featured': True, 'loc_name': 'Asokoro'
            },
            {
                'title': 'Spacious 3-Bedroom Apartment',
                'type': 'Apartment', 'bedrooms': 3, 'bathrooms': 3, 'living_rooms': 1, 'garages': 1, 'guests': 6,
                'status': 'rent', 'price': 180000,
                'description': 'Well-maintained 3-bedroom apartment. Modern kitchen...',
                'featured': True, 'loc_name': 'Wuse Zone 2'
            },
            {
                'title': 'Modern 4-Bedroom Duplex',
                'type': 'Duplex', 'bedrooms': 4, 'bathrooms': 4, 'living_rooms': 2, 'garages': 2, 'guests': 8,
                'status': 'sale', 'price': 85000000,
                'description': 'Contemporary duplex in gated estate. Open-plan living...',
                'featured': False, 'loc_name': 'Gwarimpa'
            },
            {
                'title': 'Elegant 2-Bedroom Terrace',
                'type': 'Terrace', 'bedrooms': 2, 'bathrooms': 2, 'living_rooms': 1, 'garages': 1, 'guests': 4,
                'status': 'rent', 'price': 120000,
                'description': 'Charming terrace house with modern amenities...',
                'featured': False, 'loc_name': 'LifeCamp'
            },
            # 15 More properties (to reach 20)
             {
                'title': 'Cozy 1-Bedroom Studio', 'type': 'Apartment', 'bedrooms': 1, 'bathrooms': 1, 'living_rooms': 1, 'garages': 1, 'guests': 2,
                'status': 'rent', 'price': 65000, 'description': 'Perfect for singles. Fully furnished...', 'featured': True, 'loc_name': 'Wuse Zone 1'
            },
            {
                'title': 'Luxury Serviced 2-Bed', 'type': 'Apartment', 'bedrooms': 2, 'bathrooms': 2, 'living_rooms': 1, 'garages': 1, 'guests': 4,
                'status': 'rent', 'price': 150000, 'description': 'Serviced apartment with gym and pool...', 'featured': True, 'loc_name': 'Jabi'
            },
             {
                'title': '3-Bed Detached Bungalow', 'type': 'Bungalow', 'bedrooms': 3, 'bathrooms': 2, 'living_rooms': 1, 'garages': 2, 'guests': 6,
                'status': 'sale', 'price': 45000000, 'description': 'Spacious bungalow on large plot...', 'featured': False, 'loc_name': 'Kubwa'
            },
            {
                'title': 'Premium 5-Bed Duplex', 'type': 'Duplex', 'bedrooms': 5, 'bathrooms': 5, 'living_rooms': 2, 'garages': 2, 'guests': 10,
                'status': 'sale', 'price': 120000000, 'description': 'Magnificent duplex with cinema room...', 'featured': True, 'loc_name': 'Maitama'
            },
            {
                'title': 'Affordable 2-Bed Flat', 'type': 'Apartment', 'bedrooms': 2, 'bathrooms': 2, 'living_rooms': 1, 'garages': 1, 'guests': 4,
                'status': 'rent', 'price': 95000, 'description': 'Clean and affordable flat...', 'featured': False, 'loc_name': 'Dutse'
            },
             {
                'title': 'Executive 3-Bed Apt', 'type': 'Apartment', 'bedrooms': 3, 'bathrooms': 3, 'living_rooms': 1, 'garages': 1, 'guests': 6,
                'status': 'rent', 'price': 200000, 'description': 'Executive apartment with gym and pool...', 'featured': False, 'loc_name': 'Garki'
            },
            {
                'title': 'Luxury 4-Bed Villa', 'type': 'Villa', 'bedrooms': 4, 'bathrooms': 5, 'living_rooms': 2, 'garages': 2, 'guests': 8,
                'status': 'sale', 'price': 280000000, 'description': 'Exquisite villa with private garden...', 'featured': True, 'loc_name': 'Asokoro'
            },
            {
                'title': 'Modern 1-Bed Loft', 'type': 'Apartment', 'bedrooms': 1, 'bathrooms': 1, 'living_rooms': 1, 'garages': 1, 'guests': 2,
                'status': 'rent', 'price': 80000, 'description': 'Stylish loft with high ceilings...', 'featured': False, 'loc_name': 'Jahi'
            },
            {
                'title': '4-Bed Terrace Duplex', 'type': 'Terrace', 'bedrooms': 4, 'bathrooms': 4, 'living_rooms': 2, 'garages': 2, 'guests': 8,
                'status': 'sale', 'price': 95000000, 'description': 'Spacious terrace with 24/7 power...', 'featured': False, 'loc_name': 'Gwarimpa'
            },
            {
                'title': 'Compact 2-Bed Apt', 'type': 'Apartment', 'bedrooms': 2, 'bathrooms': 2, 'living_rooms': 1, 'garages': 1, 'guests': 4,
                'status': 'rent', 'price': 110000, 'description': 'Well-designed compact apartment...', 'featured': False, 'loc_name': 'Lokogoma'
            },
            {
                'title': '6-Bed Mansion', 'type': 'Villa', 'bedrooms': 6, 'bathrooms': 7, 'living_rooms': 3, 'garages': 3, 'guests': 12,
                'status': 'sale', 'price': 650000000, 'description': 'Mansion with tennis court...', 'featured': True, 'loc_name': 'Maitama'
            },
            {
                'title': 'Standard 3-Bed Flat', 'type': 'Apartment', 'bedrooms': 3, 'bathrooms': 2, 'living_rooms': 1, 'garages': 1, 'guests': 6,
                'status': 'rent', 'price': 140000, 'description': 'Standard flat in serene area...', 'featured': False, 'loc_name': 'Gudu'
            },
             {
                'title': 'Elegant 3-Bed Penthouse', 'type': 'Penthouse', 'bedrooms': 3, 'bathrooms': 4, 'living_rooms': 1, 'garages': 2, 'guests': 6,
                'status': 'rent', 'price': 350000, 'description': 'Top-floor penthouse with city views...', 'featured': True, 'loc_name': 'Wuse Zone 2'
            },
            {
                'title': '2-Bed Bungalow', 'type': 'Bungalow', 'bedrooms': 2, 'bathrooms': 2, 'living_rooms': 1, 'garages': 1, 'guests': 4,
                'status': 'sale', 'price': 32000000, 'description': 'Affordable bungalow...', 'featured': False, 'loc_name': 'Kado'
            },
            {
                'title': 'Deluxe 5-Bed Duplex', 'type': 'Duplex', 'bedrooms': 5, 'bathrooms': 6, 'living_rooms': 2, 'garages': 2, 'guests': 10,
                'status': 'rent', 'price': 450000, 'description': 'Deluxe duplex with BQ...', 'featured': False, 'loc_name': 'Maitama'
            }
        ]

        # Create properties
        created_count = 0
        for i, prop_data in enumerate(properties_data):
            # Extract location name to find object, default to random if specific not found/provided
            loc_name = prop_data.pop('loc_name', random.choice(list(locations_map.keys())))
            # Fuzzy match or direct
            location_obj = None
            for key in locations_map:
                if key.lower() in loc_name.lower() or loc_name.lower() in key.lower():
                    location_obj = locations_map[key]
                    break
            if not location_obj:
               location_obj = locations_map[random.choice(list(locations_map.keys()))]
            
            # Add fields
            prop_data['location'] = f"{location_obj.name}, Abuja"
            prop_data['location_data'] = location_obj
            prop_data['entity'] = random.choice(entities)
            prop_data['amenities'] = random.choice(amenities_options)
            prop_data['agent'] = random.choice(agents)
            prop_data['currency'] = '₦'
            prop_data['is_active'] = True

            # Generate unique ID - SKIPPED since id is UUID
            # prop_id = f"{prop_data['location'].split(',')[0].lower().replace(' ', '-')}-{prop_data['type'].lower()}-{i+1}"
            # prop_data['id'] = prop_id

            # Area
            if prop_data['status'] == 'sale':
                prop_data['area'] = random.randint(150, 500)
            else: 
                prop_data['area'] = random.randint(50, 200)

            try:
                # Use title as pseudo-unique key for get_or_create to avoid duplicates if re-run
                property_obj, created = Property.objects.get_or_create(
                    title=prop_data['title'],
                    defaults=prop_data
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Created property: {property_obj.title}'))
                    
                    # Create 3-5 images for the property
                    num_images = random.randint(3, 5)
                    selected_images = random.sample(image_urls, num_images)
                    
                    for idx, img_url in enumerate(selected_images):
                        PropertyImage.objects.create(
                            property=property_obj,
                            image=img_url,  # CloudinaryField will accept URL string
                            is_primary=(idx == 0),
                            order=idx
                        )
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating property {prop_data["title"]}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} properties with images!'))

