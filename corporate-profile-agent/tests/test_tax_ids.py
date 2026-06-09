from corporate_profile_agent import tax_ids


def test_cnpj_valid():
    result = tax_ids.validate("BR", "11.222.333/0001-81")
    assert result.valid
    assert result.normalized == "11222333000181"


def test_cnpj_bad_checksum():
    assert not tax_ids.validate("BR", "11.222.333/0001-82").valid


def test_cnpj_repeated_digits_rejected():
    assert not tax_ids.validate("BR", "00000000000000").valid


def test_rut_valid():
    result = tax_ids.validate("CL", "12.345.678-5")
    assert result.valid
    assert result.normalized == "12345678-5"


def test_rut_k_check_digit_format():
    # DV may be K; a wrong DV must fail.
    assert not tax_ids.validate("CL", "12.345.678-K").valid


def test_nit_valid_ecopetrol():
    result = tax_ids.validate("CO", "899.999.068-1")
    assert result.valid
    assert result.normalized == "899999068-1"


def test_nit_bad_checksum():
    assert not tax_ids.validate("CO", "899999068-2").valid


def test_cuit_valid():
    result = tax_ids.validate("AR", "20-12345678-6")
    assert result.valid
    assert result.normalized == "20-12345678-6"


def test_cuit_bad_checksum():
    assert not tax_ids.validate("AR", "20-12345678-7").valid


def test_ruc_valid_company():
    result = tax_ids.validate("PE", "20100070970")
    assert result.valid


def test_ruc_bad_prefix():
    assert not tax_ids.validate("PE", "30100070970").valid


def test_rfc_company_format():
    result = tax_ids.validate("MX", "ABC 991231 XY9")
    assert result.valid
    assert result.reason == "company"


def test_rfc_individual_format():
    assert tax_ids.validate("MX", "ABCD991231XY9").valid


def test_rfc_invalid_date():
    assert not tax_ids.validate("MX", "ABC991341XY9").valid


def test_unsupported_country():
    assert not tax_ids.validate("US", "12-3456789").valid
