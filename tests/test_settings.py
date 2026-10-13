from settings import fq


def test_fully_qualified_name():
    assert fq("pm_dev", "cmapss", "bronze_train") == "`pm_dev`.`cmapss`.`bronze_train`"
