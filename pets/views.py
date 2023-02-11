from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView, Request, Response, status
from rest_framework.pagination import PageNumberPagination

from .serializers import PetSerializer, GroupSerializer, TraitSerializer

from .models import Pet
from groups.models import Group
from traits.models import Trait


class PetView(APIView, PageNumberPagination):
    def post(self, request: Request):
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pet_dict = serializer.validated_data

        group_dict = pet_dict.pop("group")

        traits_dict = pet_dict.pop("traits")

        group = Group.objects.filter(
            scientific_name__iexact=group_dict["scientific_name"]
        ).first() or Group.objects.create(**group_dict)

        pet = Pet.objects.create(**pet_dict, group=group)

        for trait in traits_dict:
            trait_found = Trait.objects.filter(name__iexact=trait["name"]).first()

            if not trait_found:
                trait_found = Trait.objects.create(**trait)

            pet.traits.add(trait_found)

        pet_to_return = PetSerializer(pet)

        return Response(pet_to_return.data, status.HTTP_201_CREATED)

    def get(self, request: Request):
        trait_param = request.query_params.get("trait")

        pets = (
            Pet.objects.all().filter(traits__name=trait_param)
            if trait_param
            else Pet.objects.all()
        )

        result_page = self.paginate_queryset(pets, request, view=self)

        pets_to_return = PetSerializer(result_page, many=True)

        return self.get_paginated_response(pets_to_return.data)


class PetDetailView(APIView):
    def get(self, request: Request, pet_id):
        pet = get_object_or_404(Pet, pk=pet_id)

        pet_to_return = PetSerializer(pet)

        return Response(pet_to_return.data, status.HTTP_200_OK)

    def delete(self, request: Request, pet_id):
        pet = get_object_or_404(Pet, pk=pet_id)

        pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request: Request, pet_id):
        pet = get_object_or_404(Pet, pk=pet_id)

        validate_pet_update = PetSerializer(data=request.data, partial=True)
        validate_pet_update.is_valid(raise_exception=True)

        group_dict = validate_pet_update.validated_data.pop("group", None)
        traits_dict = validate_pet_update.validated_data.pop("traits", None)
        pet_dict = validate_pet_update.validated_data

        for key, value in pet_dict.items():
            setattr(pet, key, value)

        if group_dict:
            group = Group.objects.filter(
                scientific_name__iexact=group_dict["scientific_name"]
            ).first() or Group.objects.create(**group_dict)

            pet.group = group

        if traits_dict:
            pet.traits.set([])
            for trait in traits_dict:
                trait_found = Trait.objects.filter(name__iexact=trait["name"]).first()

                if not trait_found:
                    trait_found = Trait.objects.create(**trait)

                pet.traits.add(trait_found)

        pet.save()

        pet_to_return = PetSerializer(pet)

        return Response(pet_to_return.data, status.HTTP_200_OK)
