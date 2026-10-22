from django.db import migrations


def create_cache_table(apps, schema_editor):
    from django.core.management.commands.createcachetable import Command

    command = Command()
    command.verbosity = 0
    command.create_table(schema_editor.connection.alias, "caloreat_cache", False)


def drop_cache_table(apps, schema_editor):
    quote_name = schema_editor.connection.ops.quote_name
    schema_editor.execute(f"DROP TABLE IF EXISTS {quote_name('caloreat_cache')}")


class Migration(migrations.Migration):
    dependencies = [("main", "0004_calorieprofile_foodentry")]
    operations = [migrations.RunPython(create_cache_table, drop_cache_table)]
