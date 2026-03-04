from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_remove_ingreso_id_producto_remove_ingreso_id_usuario_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Familia',
            new_name='Gerencia',
        ),
        migrations.RenameField(
            model_name='producto',
            old_name='familia',
            new_name='gerencia',
        ),
        migrations.AlterField(
            model_name='gerencia',
            name='padre',
            field=models.ForeignKey(
                blank=True,
                help_text='Gerencia padre en caso de ser subcategoría.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='subgerencias',
                to='app.gerencia',
            ),
        ),
        migrations.AlterModelOptions(
            name='gerencia',
            options={'verbose_name': 'Gerencia', 'verbose_name_plural': 'Gerencias'},
        ),
        migrations.AlterField(
            model_name='producto',
            name='gerencia',
            field=models.ForeignKey(
                help_text='Gerencia o subgerencia a la que pertenece el producto.',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='productos',
                to='app.gerencia',
            ),
        ),
    ]
