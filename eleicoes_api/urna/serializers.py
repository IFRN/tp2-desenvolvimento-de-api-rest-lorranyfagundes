import re
from django.utils import timezone
from rest_framework import serializers
from .models import *
from .serializers import *

class EleitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Eleitor
        fields = '__all__'

    def validate_cpf(self, value):
        padrao = r'^\d{3}\.\d{3}\.\d{3}-\d{2}$'
        if not re.match(padrao, value):
            raise serializers.ValidationError("O CPF deve estar no formato 000.000.000-00")
        return value

class EleicaoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_candidatos = serializers.SerializerMethodField()
    total_aptos = serializers.SerializerMethodField()

    class Meta:
        model = Eleicao
        fields = [
            'titulo', 
            'descricao', 
            'tipo',
            'data_inicio', 
            'data_fim',
            'status', 
            'status_display',
            'permite_branco',
            'criada_por',
            'total_candidatos',
            'total_aptos',
        ]
    def validate(self, data):
        status = data.get('status')
        if status == 'aberta':
            if self.instance and self.instance.candidatos.count()<2:
                raise serializers.ValidationError("Não é permitido abrir eleição com menos de 2 candidatos...")
        return data

    def get_total_candidatos(self, obj):
        return obj.candidatos.count()

    def get_total_aptos(self, obj):
        return obj.aptidoes.count()

class CandidatoSerializer(serializers.ModelSerializer):
    eleicao_titulo = serializers.CharField(source='eleicao.titulo', read_only=True)

    class Meta:
        model = Candidato
        fields = [
            'eleicao',
            'eleicao_titulo',
            'numero',
            'nome',
            'nome_urna',
            'partido_ou_chapa',
            'proposta',
            'foto_url',
        ]

    def validate_numero(self, value):
        if value == 0:
            raise serializers.ValidationError("zero é reservado para voto em branco.")
        return value

class AptidaoEleitorSerializer(serializers.ModelSerializer):
    eleitor_nome = serializers.CharField(source='eleitor.nome', read_only=True)
    eleicao_titulo = serializers.CharField(source='eleicao.titulo', read_only=True)

    class Meta:
        model = AptidaoEleitor
        fields = [
            'eleitor',
            'eleitor_nome',
            'eleicao',
            'eleicao_titulo',
            'data_inclusao',
        ]

class RegistroVotacaoSerializer(serializers.ModelSerializer):
    eleitor_nome = serializers.CharField(source='eleitor.nome', read_only=True)
    eleicao_titulo = serializers.CharField(source='eleicao.titulo', read_only=True)

    class Meta:
        model = RegistroVotacao
        fields = [
            'eleitor',
            'eleitor_nome',
            'eleicao',
            'eleicao_titulo',
            'data_hora',
        ]
        read_only_fields = ['eleitor',
            'eleitor_nome',
            'eleicao',
            'eleicao_titulo',
            'data_hora',
        ]

class VotoSerializer(serializers.ModelSerializer):
    candidato_nome_urna = serializers.CharField(source='candidato.nome_urna', read_only=True, allow_null=True)
    em_branco_display = serializers.SerializerMethodField()

    class Meta:
        model = Voto
        fields = [
            'eleicao',
            'candidato',
            'candidato_nome_urna',
            'em_branco',
            'em_branco_display',
            'data_hora',
        ] #não coloquei o comprovante_hash 
        read_only_fields = [
            'eleicao',
            'candidato',
            'candidato_nome_urna',
            'em_branco',
            'em_branco_display',
            'data_hora'
            ]  

    def get_em_branco_display(self, obj):
        return 'BRANCO' if obj.em_branco else None

class VotacaoInputSerializer(serializers.Serializer): #serializer dedicado APENAS para o endpoint /votar/
    eleitor_id = serializers.IntegerField()
    eleicao_id = serializers.IntegerField()
    candidato_id = serializers.IntegerField(required=False, allow_null=True)
    em_branco = serializers.BooleanField(default=False)

    def validate(self, data):
        agora = timezone.now()
        
        #(a) eleição existe e está com status='aberta'
        try:
            eleicao = Eleicao.objects.get(pk=data['eleicao_id'])
        except Eleicao.DoesNotExist:
            raise serializers.ValidationError("Eleição não encontrada")
        
        if eleicao.status != 'aberta':
            raise serializers.ValidationError("Esta eleição não está aberta para votação")

        #(b) data atual está entre data_inicio e data_fim
        if not (eleicao.data_inicio <= agora <= eleicao.data_fim):
            raise serializers.ValidationError("A eleição não está no período de votação")

        #(c) eleitor está apto na eleição
        try:
            eleitor = Eleitor.objects.get(pk=data['eleitor_id'], ativo=True)
        except Eleitor.DoesNotExist:
            raise serializers.ValidationError("Eleitor não encontrado ou inativo")
            
        if not AptidaoEleitor.objects.filter(eleitor=eleitor, eleicao=eleicao).exists():
            raise serializers.ValidationError("Este eleitor não está apto para votar nesta eleição")

        #(d) eleitor ainda não votou;
        if RegistroVotacao.objects.filter(eleitor=eleitor, eleicao=eleicao).exists():
            raise serializers.ValidationError("O eleitor já exerceu o voto nesta eleição")

        #(e) candidato (se fornecido) pertence à eleição;
        candidato_id = data.get('candidato_id')
        em_branco = data.get('em_branco')

        if candidato_id:
            try:
                candidato = Candidato.objects.get(pk=candidato_id)
                if candidato.eleicao != eleicao:
                    raise serializers.ValidationError("Este candidato não pertence a esta eleição")
            except Candidato.DoesNotExist:
                raise serializers.ValidationError("Candidato não encontrado")

        #(f) exatamente um entre candidato_id e em_branco=True foi informado
        if candidato_id and em_branco:
            raise serializers.ValidationError("Não é possível votar em um candidato e em branco ao mesmo tempo!")
        if not candidato_id and not em_branco:
            raise serializers.ValidationError("Você deve escolher um candidato ou votar em branco!")

        return data