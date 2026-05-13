from django.db import models
from django.core.exceptions import ValidationError


# Eleitor, Eleicao, Candidato, AptidaoEleitor, RegistroVotacao, Voto

class Eleitor(models.Model):
    nome = models.CharField(max_length=150) #nome do eleitor
    email = models.EmailField(unique=True) #email do eleitor
    cpf = models.CharField(max_length=14, unique=True) #cpf do eleitor - ver formato dps
    data_nascimento = models.DateField() #data de nascimento do eleitor
    ativo = models.BooleanField(default=True) #mostra se eleitor está ativo
    data_cadastro = models.DateTimeField(auto_now_add=True) #data de cadastro do eleitor

    def __str__(self):
        return self.nome

class Eleicao(models.Model):
    tipos_eleicao = [
        ('estudantil', 'Estudantil'),
        ('sindical', 'Sindical'),        
        ('associacao', 'Associação'),
        ('condominio', 'Condomínio'),
        ('conselho', 'Conselho'),
        ('Outra', 'Outra'),
    ]
    status_eleicao = [
        ('rascunho', 'Rascunho'),
        ('aberta', 'Aberta'),
        ('encerrada', 'Encerrada'),
        ('apurada', 'Apurada'),
    ]
    titulo = models.CharField(max_length=200) #titulo da eleição
    descricao = models.TextField(blank=True) #descrição da eleição
    tipo = models.CharField(max_length=50, choices=tipos_eleicao) #tipo da eleição
    data_inicio = models.DateTimeField() #data de início da eleição
    data_fim = models.DateTimeField() #data de fim da eleição
    status = models.CharField(max_length=50, choices=status_eleicao, default='rascunho') #status da eleição
    permite_branco = models.BooleanField(default=True) #diz se permite voto em branco
    criada_por = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='eleicoes_criadas') #administrador da eleição    
    
    def clean(self):
        super().clean()
        if self.data_inicio >= self.data_fim:
            raise ValidationError("A data de fim precisa ser depois da data de início.")

        if self.pk:
            status_antigo = Eleicao.objects.get(pk=self.pk).status
            ordem = [s[0] for s in self.status_eleicao] # s[0] é o valor do choice
            if ordem.index(self.status) < ordem.index(status_antigo):
                raise ValidationError(f"O status não pode voltar de {status_antigo} para {self.status}.")
      
    def __str__(self):
        return self.titulo

class Candidato(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='candidatos') #eleição que o candidato pertence
    numero = models.PositiveIntegerField() #número de exibição do candidato
    nome = models.CharField(max_length=150) #nome do candidato
    nome_urna = models.CharField(max_length=50) #nome da urna?
    partido_ou_chapa = models.CharField(max_length=100, blank=True) #partido/chapa do candidato
    proposta = models.TextField(blank=True) #proposta do candidato
    foto_url = models.URLField(blank=True) #url da foto do candidato

    class Meta:
        unique_together = ('eleicao', 'numero') #números são únicos por eleição

    def __str__(self):
        return f"{self.nome} - {self.eleicao.titulo}"

class AptidaoEleitor(models.Model):
    eleitor = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='aptidoes') #eleitor que tem a aptidão
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='aptidoes') #eleição para a qual o eleitor é apto
    data_inclusao = models.DateTimeField(auto_now_add=True) #data de inclusão da aptidão

    class Meta:
        unique_together = ('eleitor', 'eleicao')
    
    def __str__(self):
        return f"{self.eleitor} - {self.eleicao}"

class RegistroVotacao(models.Model):
    eleitor = models.ForeignKey(Eleitor, on_delete=models.PROTECT, related_name='registros_votacao') #eleitor que fez o voto
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='registros_votacao') #eleição na qual o voto foi feito
    data_hora = models.DateTimeField(auto_now_add=True) #data e hora do registro de votação

    class Meta:
        unique_together = ('eleitor', 'eleicao')

    def __str__(self):
        return f"{self.eleitor} - {self.eleicao}"

    #def __str__(self):
    #    return f"Presença: {self.eleitor.nome} na eleição {self.eleicao.titulo}"    


class Voto(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.PROTECT, related_name='votos') #eleição na qual o voto foi feito
    candidato = models.ForeignKey(Candidato, on_delete=models.PROTECT, related_name='votos', null=True, blank=True) #candidato escolhido no voto
    em_branco = models.BooleanField(default=False) #indica se o voto é em branco
    data_hora = models.DateTimeField(auto_now_add=True) #data e hora do voto
    comprovante_hash = models.CharField(max_length=64, unique=True) #hash do comprovante de voto - SHA 256 do token entregue ao eleitor

    def clean(self):
        if self.em_branco and self.candidato is not None:
            raise ValidationError(
                "Você não pode votar em um candidato e 'Em Branco' ao mesmo tempo."
            )
        if not self.em_branco and self.candidato is None:
            raise ValidationError(
                "O seu voto deve selecionar um candidato ou ser marcado como 'Em Branco'."
            )
        if self.em_branco and not self.eleicao.permite_branco:
            raise ValidationError(
                "Esta eleição não permite votos em branco."
            )

        super().clean()
    def __str__(self):
        escolha = self.candidato.nome if self.candidato else "Em Branco"
        return f"Voto #{self.id} - {escolha} ({self.eleicao.titulo})"